# scripts/build_hf_space.ps1 - Prepares Hugging Face Space Docker build directory
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Determine repo root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $scriptDir "..\..\backend")) {
    $repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
} elseif (Test-Path (Join-Path $scriptDir "..\backend")) {
    $repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
} else {
    $repoRoot = (Get-Location).Path
}

$backendDir = Join-Path $repoRoot "backend"
$targetDir = Join-Path $repoRoot "hf-space-build"

Write-Host "Preparing Hugging Face Space build directory at: $targetDir"

if (Test-Path $targetDir) {
    Remove-Item -Recurse -Force $targetDir
}
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

# Explicit copy list matching Dockerfile (no .env, tests, scripts, or venv)
Copy-Item (Join-Path $backendDir "Dockerfile") (Join-Path $targetDir "Dockerfile")
if (Test-Path (Join-Path $backendDir ".dockerignore")) {
    Copy-Item (Join-Path $backendDir ".dockerignore") (Join-Path $targetDir ".dockerignore")
}
Copy-Item (Join-Path $backendDir "pyproject.toml") (Join-Path $targetDir "pyproject.toml")
Copy-Item (Join-Path $backendDir "uv.lock") (Join-Path $targetDir "uv.lock")
Copy-Item -Recurse (Join-Path $backendDir "src") (Join-Path $targetDir "src")
Copy-Item -Recurse (Join-Path $backendDir "knowledge") (Join-Path $targetDir "knowledge")

# Create data subdirectories
New-Item -ItemType Directory -Force -Path (Join-Path $targetDir "data") | Out-Null
Copy-Item -Recurse (Join-Path $backendDir "data\catalog") (Join-Path $targetDir "data\catalog")
Copy-Item -Recurse (Join-Path $backendDir "data\demo") (Join-Path $targetDir "data\demo")

# Clean any pycache or user profiles if copied
Get-ChildItem -Path $targetDir -Recurse -Include __pycache__ -Directory | Remove-Item -Recurse -Force
Get-ChildItem -Path (Join-Path $targetDir "knowledge") -Recurse -Directory -Filter "user_*" | Remove-Item -Recurse -Force

# Write README.md with verbatim front matter
$readmeContent = @"
---
title: MediSarthi Backend
emoji: 🩺
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# MediSarthi Backend

Hugging Face Space deployment for MediSarthi FastAPI backend.
"@
Set-Content -Path (Join-Path $targetDir "README.md") -Value $readmeContent -Encoding utf8

# Secret scan on hf-space-build\
Write-Host "Running secret scan on $targetDir..."
$secretFound = $false

# Check for .env files
$envFiles = Get-ChildItem -Path $targetDir -Recurse -Filter "*.env*" -File
if ($envFiles.Count -gt 0) {
    Write-Host "SECRET SCAN FAILED: Found .env file(s) in build directory!"
    $secretFound = $true
}

# Scan content for secret patterns
$secretPatterns = @(
    "mongodb\+srv:\/\/[^:]+:[^@]+@",
    "gsk_[a-zA-Z0-9_-]+",
    "AIza[0-9A-Za-z-_]{35}",
    "sk-[a-zA-Z0-9_-]+"
)

foreach ($pattern in $secretPatterns) {
    $hits = Get-ChildItem -Path $targetDir -Recurse -File | Select-String -Pattern $pattern
    if ($hits) {
        Write-Host "SECRET SCAN FAILED: Match found for pattern $pattern"
        $hits | ForEach-Object { Write-Host "  File: $($_.Filename):$($_.LineNumber)" }
        $secretFound = $true
    }
}

if ($secretFound) {
    Write-Host "Aborting. Deleting $targetDir..."
    Remove-Item -Recurse -Force $targetDir
    exit 1
}

Write-Host "Secret scan passed: 0 secrets found."
Write-Host "Hugging Face Space build directory successfully prepared: $targetDir"

