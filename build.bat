@echo off
setlocal EnableExtensions

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "VERSION_FILE=%REPO_ROOT%\app_version.txt"

if not exist "%VERSION_FILE%" (
    > "%VERSION_FILE%" echo 1.0.0
)

set /p CURRENT_VERSION=<"%VERSION_FILE%"
echo Current version: %CURRENT_VERSION%
set /p UPDATE_VERSION="Update version before build? [y/N]: "
if /I "%UPDATE_VERSION%"=="Y" (
    set /p NEW_VERSION="Enter new version [%CURRENT_VERSION%]: "
    if not "%NEW_VERSION%"=="" (
        > "%VERSION_FILE%" echo %NEW_VERSION%
        set "CURRENT_VERSION=%NEW_VERSION%"
    )
)

powershell -ExecutionPolicy Bypass -File "%REPO_ROOT%\scripts\sync_version.ps1"
if errorlevel 1 (
    echo Version synchronization failed.
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%REPO_ROOT%\scripts\build_ankiaddon.ps1"
if errorlevel 1 (
    echo Packaging failed.
    exit /b 1
)

echo Upload packages built in: "%REPO_ROOT%\dist"
echo Build completed.
exit /b 0
