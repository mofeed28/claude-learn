"""CLI entry point — orchestrates the scraping pipeline and outputs JSON.

Usage:
    python -m scraper "stripe" --mode default
    python -m scraper "hono" --mode deep --verbose
    python -m scraper "fastapi" --output result.json

Outputs structured JSON to stdout (or file) that /learn can consume.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from urllib.parse import urlparse

from .config import ScrapeConfig, SCORE_OFFICIAL_API, SCORE_SITEMAP_DOC, SCORE_OFFICIAL_GUIDE, SCORE_GITHUB_README
from .queue import URLQueue, ScoredURL
from .fetcher import Fetcher, FetchResult
from .extractor import extract_content, content_similarity, ExtractedContent
from .discovery import (
    parse_sitemap_urls, filter_doc_urls, parse_robots_txt,
    extract_doc_links, find_sitemap_urls, is_disallowed,
    find_changelog_urls, detect_version, extract_changelog_entries,
)

log = logging.getLogger("claude-learn-scraper")


def _progress(msg: str, verbose: bool):
    """Print progress to stderr (so stdout stays clean for JSON)."""
    if verbose:
        print(f"  [scraper] {msg}", file=sys.stderr, flush=True)


async def run_scraper(topic: str, config: ScrapeConfig, initial_urls: list[str] | None = None, verbose: bool = False) -> dict:
    """Run the full scraping pipeline for a topic.

    Returns a structured dict with all scraped content.
    """
    start_time = time.monotonic()
    queue = URLQueue(max_size=config.max_urls)
    fetcher = Fetcher(config)
    all_content: list[dict] = []
    disallowed_paths: list[str] = []
    detected_version: str | None = None
    changelog_entries: list[dict] = []
    stats = {
        "urls_discovered": 0,
        "urls_fetched": 0,
        "urls_cached": 0,
        "urls_failed": 0,
        "soft_failures": 0,
        "urls_skipped_disallowed": 0,
        "urls_skipped_dedup": 0,
    }

    try:
        # Seed the queue with initial URLs
        if initial_urls:
            for url in initial_urls:
                queue.add(url, source="initial")
            _progress(f"Seeded queue with {len(initial_urls)} URL(s)", verbose)

        # Phase 1: Sitemap & robots.txt discovery
        docs_domains = set()
        for url in (initial_urls or []):
            parsed = urlparse(url)
            if parsed.netloc:
                docs_domains.add(f"{parsed.scheme}://{parsed.netloc}")

        for base in docs_domains:
            _progress(f"Discovering sitemaps for {base}...", verbose)
            sitemap_candidates = find_sitemap_urls(base)
            sitemap_results = await fetcher.fetch_batch(sitemap_candidates)

            for result in sitemap_results:
                if not result.success:
                    continue

                if result.url.endswith("robots.txt"):
                    sitemaps, disallowed = parse_robots_txt(result.content)
                    disallowed_paths.extend(disallowed)
                    _progress(f"  robots.txt: {len(sitemaps)} sitemap(s), {len(disallowed)} disallow rule(s)", verbose)
                    for sm_url in sitemaps:
                        sm_result = await fetcher.fetch_one(sm_url)
                        if sm_result.success:
                            urls = filter_doc_urls(parse_sitemap_urls(sm_result.content))
                            added = queue.add_many(urls, score=SCORE_SITEMAP_DOC, source="sitemap")
                            _progress(f"  sitemap {sm_url}: {added} doc URL(s) added", verbose)
                else:
                    urls = filter_doc_urls(parse_sitemap_urls(result.content))
                    added = queue.add_many(urls, score=SCORE_SITEMAP_DOC, source="sitemap")
                    _progress(f"  {result.url}: {added} doc URL(s) added", verbose)

        stats["urls_discovered"] = queue.total_count
        _progress(f"Discovery complete: {queue.total_count} URL(s) in queue", verbose)

        # Phase 2: Fetch pages in batches
        seen_texts: list[str] = []
        batch_num = 0

        while queue.pending_count > 0 and len(all_content) < config.max_urls:
            batch = queue.get_batch(size=config.concurrency)
            if not batch:
                break

            batch_num += 1
            urls_to_fetch = []
            for entry in batch:
                if is_disallowed(entry.url, disallowed_paths):
                    stats["urls_skipped_disallowed"] += 1
                else:
                    urls_to_fetch.append(entry.url)

            if not urls_to_fetch:
                queue.mark_batch_fetched(batch)
                continue

            _progress(f"Batch {batch_num}: fetching {len(urls_to_fetch)} URL(s)...", verbose)
            results = await fetcher.fetch_batch(urls_to_fetch)
            queue.mark_batch_fetched(batch)

            for result in results:
                stats["urls_fetched"] += 1

                if result.from_cache:
                    stats["urls_cached"] += 1

                if not result.success:
                    if result.error == "soft_failure":
                        stats["soft_failures"] += 1
                        _progress(f"  SOFT FAIL: {result.url}", verbose)
                    else:
                        stats["urls_failed"] += 1
                        _progress(f"  FAILED: {result.url} ({result.error})", verbose)
                    continue

                extracted = extract_content(result.content, base_url=result.url)

                # Dedup: skip if >90% similar to already-seen content
                is_dup = False
                for seen in seen_texts:
                    if content_similarity(extracted.text, seen) > 0.9:
                        is_dup = True
                        break

                if is_dup:
                    stats["urls_skipped_dedup"] += 1
                    _progress(f"  DEDUP: {result.url}", verbose)
                    continue

                seen_texts.append(extracted.text[:5000])

                # Version detection from page content
                if not detected_version:
                    detected_version = detect_version(extracted.text, topic)
                    if detected_version:
                        _progress(f"  Detected version: {detected_version}", verbose)

                cache_label = " (cached)" if result.from_cache else ""
                _progress(f"  OK: {result.url} ({extracted.word_count} words, {len(extracted.code_blocks)} code blocks){cache_label}", verbose)

                all_content.append({
                    "url": result.url,
                    "title": extracted.title,
                    "text": extracted.text[:50000],
                    "code_blocks": extracted.code_blocks[:50],
                    "headings": extracted.headings[:100],
                    "tables": extracted.tables[:30],
                    "word_count": extracted.word_count,
                    "from_cache": result.from_cache,
                    "fetch_time_ms": result.fetch_time_ms,
                })

                # Link crawling (depth-1)
                for link in extracted.links:
                    queue.add(link, score=SCORE_OFFICIAL_GUIDE, source=f"crawled:{result.url}", depth=1)

        # Phase 3: Changelog discovery
        _progress("Checking for changelogs...", verbose)
        for base in docs_domains:
            changelog_candidates = find_changelog_urls(base, topic)
            for url in changelog_candidates[:4]:  # limit probes
                result = await fetcher.fetch_one(url)
                if result.success and len(result.content) > 200:
                    extracted = extract_content(result.content, base_url=url)
                    entries = extract_changelog_entries(extracted.text)
                    if entries:
                        changelog_entries = entries
                        if not detected_version and entries:
                            detected_version = entries[0]["version"]
                        _progress(f"  Found changelog: {url} ({len(entries)} entries)", verbose)
                        break

        stats["urls_discovered"] = queue.total_count
        elapsed = time.monotonic() - start_time

        _progress(f"Done: {len(all_content)} pages in {elapsed:.1f}s", verbose)

        return {
            "topic": topic,
            "mode": config.mode,
            "version": detected_version,
            "changelog": changelog_entries,
            "pages": all_content,
            "stats": {
                **stats,
                "pages_extracted": len(all_content),
                "total_time_seconds": round(elapsed, 2),
                "cache_hits": stats["urls_cached"],
            },
            "urls_fetched": [page["url"] for page in all_content],
        }

    finally:
        await fetcher.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="claude-learn scraper — fetch and extract documentation",
        prog="claude-learn-scraper",
    )
    parser.add_argument("topic", help="Technology/library to scrape docs for")
    parser.add_argument(
        "--mode", choices=["quick", "default", "deep"], default="default",
        help="Scraping depth mode (default: default)",
    )
    parser.add_argument(
        "--urls", nargs="*", default=[],
        help="Initial URLs to seed the scraper with",
    )
    parser.add_argument(
        "--cache-dir", default="~/.cache/claude-learn",
        help="Cache directory (default: ~/.cache/claude-learn)",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Disable caching",
    )
    parser.add_argument(
        "--timeout", type=float, default=15.0,
        help="Request timeout in seconds (default: 15)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print progress to stderr",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Write JSON output to file instead of stdout",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    config = ScrapeConfig(
        mode=args.mode,
        cache_dir=args.cache_dir,
        request_timeout=args.timeout,
    )

    if args.no_cache:
        config.cache_ttl = 0

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

    result = asyncio.run(run_scraper(
        topic=args.topic,
        config=config,
        initial_urls=args.urls or [],
        verbose=args.verbose,
    ))

    # Output JSON
    json_str = json.dumps(result, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        if args.verbose:
            print(f"  [scraper] Output written to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(json_str)


if __name__ == "__main__":
    main()
