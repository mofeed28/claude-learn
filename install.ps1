# claude-learn installer for Windows
# Copies /learn commands to your ~/.claude/commands directory

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

Write-Host "  Installed:" -ForegroundColor Green
Write-Host "    /learn        -> $CommandsDir\learn.md"
Write-Host "    /learn-update -> $CommandsDir\learn-update.md"
Write-Host "    /learn-list   -> $CommandsDir\learn-list.md"
Write-Host "    /learn-delete -> $CommandsDir\learn-delete.md"
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
