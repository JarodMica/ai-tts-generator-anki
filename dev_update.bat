@echo off
setlocal EnableExtensions

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"

set "TARGET_ADDON_DIR=%~1"
if "%TARGET_ADDON_DIR%"=="" (
    set "TARGET_ADDON_DIR=C:\Users\jarod\AppData\Roaming\Anki2\addons21\510081046"
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%\scripts\dev_update_addon.ps1" -TargetAddonDir "%TARGET_ADDON_DIR%"
if errorlevel 1 (
    echo Dev update failed.
    exit /b 1
)

echo Dev update completed. Restart Anki to load the updated add-on code.
exit /b 0
