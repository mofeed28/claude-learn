# claude-learn installer for Windows
# Copies /learn commands and optionally installs the Python scraper

Write-Host ""
Write-Host "  claude-learn installer" -ForegroundColor Cyan
Write-Host "  ======================" -ForegroundColor Cyan
Write-Host ""

$CommandsDir = Join-Path $env:USERPROFILE ".claude\commands"
$SourceDir = Join-Path $PSScriptRoot "commands"

# Create commands directory if it doesn't exist
if (-not (Test-Path $CommandsDir)) {
    New-Item -ItemType Directory -Path $CommandsDir -Force | Out-Null
    Write-Host "  Created $CommandsDir"
}

# Copy command files
Copy-Item "$SourceDir\learn.md" "$CommandsDir\learn.md" -Force
Copy-Item "$SourceDir\learn-update.md" "$CommandsDir\learn-update.md" -Force
Copy-Item "$SourceDir\learn-list.md" "$CommandsDir\learn-list.md" -Force
Copy-Item "$SourceDir\learn-delete.md" "$CommandsDir\learn-delete.md" -Force
Copy-Item "$SourceDir\learn-audit.md" "$CommandsDir\learn-audit.md" -Force

Write-Host "  Installed commands:" -ForegroundColor Green
Write-Host "    /learn        -> $CommandsDir\learn.md"
Write-Host "    /learn-update -> $CommandsDir\learn-update.md"
Write-Host "    /learn-list   -> $CommandsDir\learn-list.md"
Write-Host "    /learn-delete -> $CommandsDir\learn-delete.md"
Write-Host "    /learn-audit  -> $CommandsDir\learn-audit.md"
Write-Host ""

# Install Python scraper (optional but recommended)
$ScraperInstalled = $false
$PythonCmd = $null

# Find Python
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
}

if ($PythonCmd) {
    $PythonVersion = & $PythonCmd --version 2>&1
    Write-Host "  Python found: $PythonVersion"

    # Check pip
    $PipCheck = & $PythonCmd -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Installing runtime scraper..."
        & $PythonCmd -m pip install -e $PSScriptRoot --quiet 2>$null
        if ($LASTEXITCODE -eq 0) {
            $ScraperInstalled = $true
            Write-Host "  Scraper installed successfully" -ForegroundColor Green
        } else {
            & $PythonCmd -m pip install $PSScriptRoot --quiet 2>$null
            if ($LASTEXITCODE -eq 0) {
                $ScraperInstalled = $true
                Write-Host "  Scraper installed successfully" -ForegroundColor Green
            } else {
                Write-Host "  Warning: Could not install scraper via pip" -ForegroundColor Yellow
                Write-Host "  You can install manually: pip install -e $PSScriptRoot"
            }
        }
    } else {
        Write-Host "  Warning: pip not found. Scraper not installed." -ForegroundColor Yellow
        Write-Host "  Install pip, then run: pip install -e $PSScriptRoot"
    }
} else {
    Write-Host "  Warning: Python not found. Scraper not installed." -ForegroundColor Yellow
    Write-Host "  /learn will use Claude's built-in WebFetch/WebSearch (still works)."
}

Write-Host ""
if ($ScraperInstalled) {
    Write-Host "  Setup complete (with scraper)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Verify scraper: $PythonCmd -m scraper --help"
} else {
    Write-Host "  Setup complete (commands only)" -ForegroundColor Green
    Write-Host "  For better results, install the scraper: pip install -e $PSScriptRoot"
}

Write-Host ""
Write-Host "  Restart Claude Code, then try:" -ForegroundColor Yellow
Write-Host "    /learn stripe"
Write-Host "    /learn stripe --quick"
Write-Host "    /learn react:hooks --lang typescript"
Write-Host "    /learn https://github.com/honojs/hono"
Write-Host "    /learn ./path/to/api-spec.yaml"
Write-Host ""
Write-Host "  Done!" -ForegroundColor Green
Write-Host ""
