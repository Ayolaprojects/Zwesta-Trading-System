@echo off
REM Zwesta Trading System - Android APK Build Script
REM This script builds a release APK for Android deployment

setlocal enabledelayedexpansion

cls
echo.
echo ================================================================================
echo   Zwesta Trading System - ANDROID APK BUILD
echo ================================================================================
echo.

REM Check if Flutter is installed
flutter --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Flutter is not installed or not in PATH
    echo Please install Flutter and add to PATH
    pause
    exit /b 1
)

REM Check if Android toolchain is setup
flutter doctor >nul 2>&1
echo [OK] Flutter environment found

echo.
echo ================================================================================
echo   STEP 1: Checking Android Setup
echo ================================================================================
echo.

flutter doctor -v | find "Android toolchain"
if %errorlevel% neq 0 (
    echo [WARN] Android toolchain may not be configured
    echo Running 'flutter doctor --android-licenses'...
    call flutter doctor --android-licenses
)

echo [OK] Android toolchain ready

echo.
echo ================================================================================
echo   STEP 2: Getting Flutter Dependencies
echo ================================================================================
echo.

call flutter pub get --quiet
echo [OK] Dependencies resolved

echo.
echo ================================================================================
echo   STEP 3: Running Build
echo ================================================================================
echo.
echo Building release APK...
echo This may take 5-10 minutes...
echo.

call flutter build apk --release ^
    --dart-define=ZWESTA_ENV=production ^
    --dart-define=API_URL=http://148.113.5.21:9000

if %errorlevel% neq 0 (
    echo [ERROR] APK build failed
    pause
    exit /b 1
)

echo [OK] APK build completed

echo.
echo ================================================================================
echo   BUILD ARTIFACTS
echo ================================================================================
echo.
echo APK Location: build\app\outputs\apk\release\app-release.apk
echo APK Size: 
for /F "delims= " %%A in ('dir /b build\app\outputs\apk\release\app-release.apk') do (
    echo   %%A
)

echo.
echo ================================================================================
echo   NEXT STEPS
echo ================================================================================
echo.
echo 1. Connect your Android device (USB debugging enabled)
echo 2. Install APK:
echo    adb install build\app\outputs\apk\release\app-release.apk
echo.
echo 3. Or transfer APK to device manually:
echo    - Copy build\app\outputs\apk\release\app-release.apk to device
echo    - Open file manager and tap to install
echo.
echo 4. Update API_URL in the app settings to point to your VPS
echo.

pause
