"""CLI entry point — orchestrates the scraping pipeline and outputs JSON.

Usage:
    python -m scraper "stripe" --mode default --lang typescript
    python -m scraper "hono" --mode deep

Outputs structured JSON to stdout that /learn can consume.
"""

from __future__ import annotations

import argparse
import asyncio
import json
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
)


async def run_scraper(topic: str, config: ScrapeConfig, initial_urls: list[str] | None = None) -> dict:
    """Run the full scraping pipeline for a topic.

    Returns a structured dict with all scraped content.
    """
    start_time = time.monotonic()
    queue = URLQueue(max_size=config.max_urls)
    fetcher = Fetcher(config)
    all_content: list[dict] = []
    disallowed_paths: list[str] = []
    stats = {
        "urls_discovered": 0,
        "urls_fetched": 0,
        "urls_cached": 0,
        "urls_failed": 0,
        "soft_failures": 0,
    }

    try:
        # Seed the queue with initial URLs
        if initial_urls:
            for url in initial_urls:
                queue.add(url, source="initial")

        # Phase 1: Sitemap & robots.txt discovery
        # Find the docs domain from initial URLs
        docs_domains = set()
        for url in (initial_urls or []):
            parsed = urlparse(url)
            if parsed.netloc:
                docs_domains.add(f"{parsed.scheme}://{parsed.netloc}")

        for base in docs_domains:
            sitemap_candidates = find_sitemap_urls(base)
            sitemap_results = await fetcher.fetch_batch(sitemap_candidates)

            for result in sitemap_results:
                if not result.success:
                    continue

                if result.url.endswith("robots.txt"):
                    sitemaps, disallowed = parse_robots_txt(result.content)
                    disallowed_paths.extend(disallowed)
                    for sm_url in sitemaps:
                        sm_result = await fetcher.fetch_one(sm_url)
                        if sm_result.success:
                            urls = filter_doc_urls(parse_sitemap_urls(sm_result.content))
                            queue.add_many(urls, score=SCORE_SITEMAP_DOC, source="sitemap")
                else:
                    # Direct sitemap.xml
                    urls = filter_doc_urls(parse_sitemap_urls(result.content))
                    queue.add_many(urls, score=SCORE_SITEMAP_DOC, source="sitemap")

        stats["urls_discovered"] = queue.total_count

        # Phase 2: Fetch pages in batches
        seen_texts: list[str] = []  # for dedup

        while queue.pending_count > 0 and len(all_content) < config.max_urls:
            batch = queue.get_batch(size=config.concurrency)
            if not batch:
                break

            urls_to_fetch = [
                entry.url for entry in batch
                if not is_disallowed(entry.url, disallowed_paths)
            ]

            if not urls_to_fetch:
                queue.mark_batch_fetched(batch)
                continue

            results = await fetcher.fetch_batch(urls_to_fetch)
            queue.mark_batch_fetched(batch)

            for result in results:
                stats["urls_fetched"] += 1

                if result.from_cache:
                    stats["urls_cached"] += 1

                if not result.success:
                    if result.error == "soft_failure":
                        stats["soft_failures"] += 1
                    else:
                        stats["urls_failed"] += 1
                    continue

                # Extract content
                extracted = extract_content(result.content, base_url=result.url)

                # Dedup: skip if >90% similar to already-seen content
                is_dup = False
                for seen in seen_texts:
                    if content_similarity(extracted.text, seen) > 0.9:
                        is_dup = True
                        break

                if is_dup:
                    continue

                seen_texts.append(extracted.text[:5000])  # keep first 5k chars for comparison

                # Store extracted content
                all_content.append({
                    "url": result.url,
                    "title": extracted.title,
                    "text": extracted.text[:50000],  # cap at 50k chars
                    "code_blocks": extracted.code_blocks[:50],  # cap at 50 blocks
                    "headings": extracted.headings[:100],
                    "tables": extracted.tables[:30],
                    "word_count": extracted.word_count,
                    "from_cache": result.from_cache,
                    "fetch_time_ms": result.fetch_time_ms,
                })

                # Phase 3: Link crawling (depth-1)
                # Extract doc links and add to queue
                for link in extracted.links:
                    queue.add(link, score=SCORE_OFFICIAL_GUIDE, source=f"crawled:{result.url}", depth=1)

        stats["urls_discovered"] = queue.total_count
        elapsed = time.monotonic() - start_time

        return {
            "topic": topic,
            "mode": config.mode,
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

    result = asyncio.run(run_scraper(
        topic=args.topic,
        config=config,
        initial_urls=args.urls or [],
    ))

    # Output JSON to stdout
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
