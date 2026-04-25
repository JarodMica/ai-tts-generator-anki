$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$rootVersionPath = Join-Path $repoRoot "app_version.txt"
$addonVersionTextPath = Join-Path $repoRoot "SentenceAudioGenerator\app_version.txt"
$addonVersionModulePath = Join-Path $repoRoot "SentenceAudioGenerator\version.py"

if (-not (Test-Path $rootVersionPath)) {
    throw "Version file not found: $rootVersionPath"
}

$version = (Get-Content -Raw $rootVersionPath).Trim()
if (-not $version) {
    throw "app_version.txt is empty."
}

if ($version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Version must match semantic form X.Y.Z. Found: $version"
}

Set-Content -Path $addonVersionTextPath -Value ($version + "`r`n") -Encoding ascii
Set-Content -Path $addonVersionModulePath -Value ("APP_VERSION = `"" + $version + "`"`r`n") -Encoding ascii

Write-Output "Version synchronized: $version"
