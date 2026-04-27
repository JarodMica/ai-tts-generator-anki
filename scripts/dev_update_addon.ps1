param(
    [string]$TargetAddonDir = "C:\Users\jarod\AppData\Roaming\Anki2\addons21\510081046"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceAddonDir = Join-Path $repoRoot "SentenceAudioGenerator"
$syncVersionScript = Join-Path $PSScriptRoot "sync_version.ps1"
$sourceManifestPath = Join-Path $sourceAddonDir "manifest.json"
$targetManifestPath = Join-Path $TargetAddonDir "manifest.json"

function Read-ManifestPackage {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Manifest not found: $Path"
    }

    $manifest = Get-Content -Raw $Path | ConvertFrom-Json
    if (-not $manifest.package) {
        throw "Manifest has no package field: $Path"
    }

    return [string]$manifest.package
}

function Copy-AddonItem {
    param(
        [System.IO.FileSystemInfo]$Item,
        [string]$DestinationRoot
    )

    if ($Item.Name -eq "__pycache__" -or $Item.Name -eq "user_files") {
        return
    }
    if (-not $Item.PSIsContainer -and $Item.Extension -eq ".pyc") {
        return
    }

    $destination = Join-Path $DestinationRoot $Item.Name
    if ($Item.PSIsContainer) {
        if (Test-Path $destination) {
            Remove-Item -Recurse -Force $destination
        }
        Copy-Item -Recurse -Force -Path $Item.FullName -Destination $destination
        Get-ChildItem -Path $destination -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force
        Get-ChildItem -Path $destination -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue |
            Remove-Item -Force
    } else {
        Copy-Item -Force -Path $Item.FullName -Destination $destination
    }
}

if (-not (Test-Path $sourceAddonDir)) {
    throw "Source add-on folder not found: $sourceAddonDir"
}
if (-not (Test-Path $TargetAddonDir)) {
    throw "Existing Anki add-on folder not found: $TargetAddonDir"
}

$sourcePackage = Read-ManifestPackage -Path $sourceManifestPath
$targetPackage = Read-ManifestPackage -Path $targetManifestPath
if ($sourcePackage -ne $targetPackage) {
    throw "Refusing to update '$TargetAddonDir': target package '$targetPackage' does not match source package '$sourcePackage'."
}

& $syncVersionScript

$preserveNames = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
[void]$preserveNames.Add("meta.json")
[void]$preserveNames.Add("user_files")

$sourceNames = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
Get-ChildItem -Path $sourceAddonDir -Force | Where-Object {
    $_.Name -ne "__pycache__" -and $_.Name -ne "user_files" -and ($_.PSIsContainer -or $_.Extension -ne ".pyc")
} | ForEach-Object {
    [void]$sourceNames.Add($_.Name)
}

Get-ChildItem -Path $TargetAddonDir -Force | ForEach-Object {
    if ($preserveNames.Contains($_.Name)) {
        return
    }
    if (-not $sourceNames.Contains($_.Name)) {
        Remove-Item -Recurse:($_.PSIsContainer) -Force -Path $_.FullName
    }
}

Get-ChildItem -Path $sourceAddonDir -Force | ForEach-Object {
    Copy-AddonItem -Item $_ -DestinationRoot $TargetAddonDir
}

Write-Output "Updated existing Anki add-on:"
Write-Output "  Source: $sourceAddonDir"
Write-Output "  Target: $TargetAddonDir"
Write-Output "Preserved target meta.json and user_files."
