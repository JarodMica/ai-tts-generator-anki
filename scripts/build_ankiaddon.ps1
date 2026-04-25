$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$addonRoot = Join-Path $repoRoot "SentenceAudioGenerator"
$distDir = Join-Path $repoRoot "dist"
$stagingDir = Join-Path $distDir "ankiaddon-staging"
$zipPath = Join-Path $distDir "SentenceAudioGenerator.zip"
$addonPath = Join-Path $distDir "SentenceAudioGenerator.ankiaddon"
$versionPath = Join-Path $repoRoot "app_version.txt"
$legacyZipPath = Join-Path $distDir "ankisentenceaudio.zip"
$legacyAddonPath = Join-Path $distDir "ankisentenceaudio.ankiaddon"
$legacyZipPath2 = Join-Path $distDir "sentenceaudiogenerator.zip"
$legacyAddonPath2 = Join-Path $distDir "sentenceaudiogenerator.ankiaddon"

if (-not (Test-Path $addonRoot)) {
    throw "Add-on folder not found: $addonRoot"
}
if (-not (Test-Path $versionPath)) {
    throw "Version file not found: $versionPath"
}

$version = (Get-Content -Raw $versionPath).Trim()
if (-not $version) {
    throw "app_version.txt is empty."
}
$versionedAddonPath = Join-Path $distDir ("SentenceAudioGenerator-" + $version + ".ankiaddon")
$legacyVersionedAddonPattern = Join-Path $distDir "ankisentenceaudio-*.ankiaddon"
$legacyVersionedAddonPattern2 = Join-Path $distDir "sentenceaudiogenerator-*.ankiaddon"

New-Item -ItemType Directory -Force -Path $distDir | Out-Null

if (Test-Path $stagingDir) {
    Remove-Item -Recurse -Force $stagingDir
}
New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null

Get-ChildItem -Path $addonRoot -Force | Where-Object {
    $_.Name -ne "__pycache__"
} | ForEach-Object {
    $target = Join-Path $stagingDir $_.Name
    if ($_.PSIsContainer) {
        Copy-Item -Recurse -Force -Path $_.FullName -Destination $target
        Get-ChildItem -Path $target -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
        Get-ChildItem -Path $target -Recurse -File -Include "*.pyc" | Remove-Item -Force
    } else {
        Copy-Item -Force -Path $_.FullName -Destination $target
    }
}

if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}
if (Test-Path $addonPath) {
    Remove-Item -Force $addonPath
}
if (Test-Path $versionedAddonPath) {
    Remove-Item -Force $versionedAddonPath
}
if (Test-Path $legacyZipPath) {
    Remove-Item -Force $legacyZipPath
}
if (Test-Path $legacyAddonPath) {
    Remove-Item -Force $legacyAddonPath
}
Remove-Item -Force $legacyVersionedAddonPattern -ErrorAction SilentlyContinue
if (Test-Path $legacyZipPath2) {
    Remove-Item -Force $legacyZipPath2
}
if (Test-Path $legacyAddonPath2) {
    Remove-Item -Force $legacyAddonPath2
}
Remove-Item -Force $legacyVersionedAddonPattern2 -ErrorAction SilentlyContinue

Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -Force
Move-Item -Force -Path $zipPath -Destination $addonPath
Copy-Item -Force -Path $addonPath -Destination $versionedAddonPath

Write-Output "Built: $addonPath"
Write-Output "Built: $versionedAddonPath"
