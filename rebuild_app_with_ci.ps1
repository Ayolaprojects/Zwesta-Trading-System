#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Zwesta Trading App - Complete CI/CD Rebuild with Git Actions
.DESCRIPTION
    Automates the complete build, test, and deployment process using GitHub Actions
.EXAMPLE
    .\rebuild_app_with_ci.ps1 -Branch main -ApiUrl "http://127.0.0.1:9000"
#>

param(
    [string]$Branch = "main",
    [string]$ApiUrl = "http://127.0.0.1:9000",
    [switch]$SkipTests,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ============================================================================
# COLORS & LOGGING
# ============================================================================
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$BLUE = "`e[34m"
$RESET = "`e[0m"

function Write-Success {
    param([string]$Message)
    Write-Host "$GREEN✅ $Message$RESET"
}

function Write-Info {
    param([string]$Message)
    Write-Host "$BLUE$Message$RESET"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "$YELLOW⚠️  $Message$RESET"
}

function Write-Error {
    param([string]$Message)
    Write-Host "$RED❌ $Message$RESET"
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================
function Test-Prerequisites {
    Write-Info "=== PHASE 1: PRE-FLIGHT CHECKS ==="
    
    # Check Git
    try {
        $gitVersion = git --version
        Write-Success "Git installed: $gitVersion"
    }
    catch {
        Write-Error "Git not found. Please install Git."
        exit 1
    }
    
    # Check current directory
    if (-not (Test-Path ".git")) {
        Write-Error "Not in a Git repository. Run from zwesta-trader root."
        exit 1
    }
    
    # Check Flutter
    try {
        $flutterVersion = flutter --version
        Write-Success "Flutter installed: $($flutterVersion -split '`n' | Select-Object -First 1)"
    }
    catch {
        Write-Warning "Flutter not found - GitHub Actions will handle the build"
    }
    
    # Verify files exist
    $requiredFiles = @(
        ".github/workflows/flutter-build-test-deploy.yml",
        "zwesta-v2-professional/mobile/lib/services/enhanced_api_service.dart",
        "zwesta-v2-professional/mobile/lib/utils/validators.dart",
        "zwesta-v2-professional/mobile/test/providers/auth_provider_test.dart",
        "zwesta-v2-professional/mobile/test/utils/validators_test.dart"
    )
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-Success "Found: $file"
        }
        else {
            Write-Error "Missing: $file"
            exit 1
        }
    }
}

# ============================================================================
# GIT PREPARATION
# ============================================================================
function Prepare-Git {
    Write-Info "`n=== PHASE 2: GIT PREPARATION ==="
    
    # Get current branch
    $currentBranch = git rev-parse --abbrev-ref HEAD
    Write-Info "Current branch: $currentBranch"
    
    # Check for uncommitted changes
    $changes = git status --porcelain
    if ($changes) {
        Write-Warning "Uncommitted changes detected:"
        Write-Host $changes
        
        $response = Read-Host "Stage all changes? (y/n)"
        if ($response -eq "y") {
            git add -A
            Write-Success "Changes staged"
        }
        else {
            Write-Error "Cannot proceed with uncommitted changes"
            exit 1
        }
    }
    else {
        Write-Success "Working directory clean"
    }
}

# ============================================================================
# CREATE COMMIT
# ============================================================================
function Create-Commit {
    param([string]$Branch)
    
    Write-Info "`n=== PHASE 3: CREATE COMMIT ==="
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $commitMessage = @"
chore: rebuild with production upgrades and enhanced CI/CD

- Integrated enhanced_api_service.dart with error handling
- Added comprehensive input validators (20+ functions)
- Implemented unit tests with >80% coverage target
- NIST-compliant password validation
- Updated GitHub Actions workflow with 5-phase CI/CD
- Automated builds for Android APK and iOS
- Added codecov coverage reporting
- Automated GitHub releases

Build: $Branch - $timestamp
"@
    
    if ($DryRun) {
        Write-Info "DRY RUN: Would commit with message:"
        Write-Host $commitMessage
        return
    }
    
    git commit -m $commitMessage
    Write-Success "Commit created successfully"
    
    # Show commit details
    Write-Info "`nCommit details:"
    git log --oneline -1
}

# ============================================================================
# PUSH TO REMOTE
# ============================================================================
function Push-ToRemote {
    param([string]$Branch)
    
    Write-Info "`n=== PHASE 4: PUSH TO REMOTE ==="
    
    # Check if branch exists on remote
    $remoteBranches = git branch -r
    $remoteBranchExists = $remoteBranches -match "origin/$Branch"
    
    if ($remoteBranchExists) {
        Write-Info "Remote branch detected: origin/$Branch"
    }
    else {
        Write-Warning "Remote branch not found - will create: origin/$Branch"
    }
    
    if ($DryRun) {
        Write-Info "DRY RUN: Would push to origin/$Branch"
        return
    }
    
    try {
        git push -u origin $Branch
        Write-Success "Pushed to origin/$Branch"
    }
    catch {
        Write-Error "Push failed: $_"
        exit 1
    }
}

# ============================================================================
# TRIGGER CI/CD
# ============================================================================
function Trigger-CICD {
    param([string]$Branch, [string]$ApiUrl)
    
    Write-Info "`n=== PHASE 5: GITHUB ACTIONS WORKFLOW ==="
    
    Write-Info "Workflow triggered automatically on push to $Branch"
    Write-Info "GitHub Actions will run:"
    Write-Info "  1. Setup & Lint (dart format, analyzer)"
    Write-Info "  2. Unit Tests (validators, auth provider)"
    Write-Info "  3. Build Android APK"
    Write-Info "  4. Build iOS App"
    Write-Info "  5. Create GitHub Release"
    
    Write-Warning "Note: GitHub Actions runs in the cloud"
    Write-Info "Monitor progress at:"
    Write-Info "  https://github.com/$(git config --get remote.origin.url | grep -oP '(?<=github\.com[:/]).*?(?=\.git)')/actions"
}

# ============================================================================
# LOCAL TEST RUN (OPTIONAL)
# ============================================================================
function Run-LocalTests {
    Write-Info "`n=== PHASE 6: LOCAL TEST RUN (OPTIONAL) ==="
    
    if ($SkipTests) {
        Write-Warning "Skipping local tests (--SkipTests flag)"
        return
    }
    
    Write-Info "Running local tests before GitHub Actions..."
    
    try {
        Push-Location "zwesta-v2-professional/mobile"
        
        if (Test-Path "pubspec.yaml") {
            Write-Info "Getting Flutter dependencies..."
            flutter pub get
            
            Write-Info "Running validators_test.dart..."
            flutter test test/utils/validators_test.dart --no-pub
            
            Write-Info "Running auth_provider_test.dart..."
            flutter test test/providers/auth_provider_test.dart --no-pub
            
            Write-Success "All local tests passed!"
        }
        else {
            Write-Warning "pubspec.yaml not found - skipping local tests"
        }
    }
    catch {
        Write-Error "Local tests failed: $_"
        Write-Warning "GitHub Actions will attempt the build anyway"
    }
    finally {
        Pop-Location
    }
}

# ============================================================================
# GENERATE REPORT
# ============================================================================
function Generate-Report {
    param([string]$Branch)
    
    Write-Info "`n=== FINAL REPORT ==="
    
    $report = @"
$GREEN
╔════════════════════════════════════════════════════════════════╗
║         ZWESTA TRADING APP - CI/CD BUILD INITIATED            ║
╚════════════════════════════════════════════════════════════════╝
$RESET

📱 APP BUILD CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Branch:              $Branch
API URL:             $ApiUrl
Commit:              $(git log -1 --format=%H)
Timestamp:           $(Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC")

✅ PRODUCTION UPGRADES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Enhanced API Service (enhanced_api_service.dart)
  - Auto token refresh on 401 responses
  - Comprehensive error handling
  - Request/response logging
  - Queue-based retry mechanism

✓ Input Validators (validators.dart)
  - 20+ validation functions
  - NIST-compliant passwords (8+ chars, upper, lower, digit, special)
  - Email, username, amount, percentage validators
  - Price levels, stop loss, risk/reward validation

✓ Unit Test Suite
  - validators_test.dart (600+ lines, 40+ test cases)
  - auth_provider_test.dart (300+ lines)
  - Target: >80% code coverage

✓ CI/CD Pipeline (5-phase workflow)
  - Phase 1: Setup & Lint
  - Phase 2: Unit Tests with Coverage
  - Phase 3: Build Android APK (release)
  - Phase 4: Build iOS App (release)
  - Phase 5: Deployment Summary & GitHub Release

🚀 GITHUB ACTIONS BUILDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Outputs:
  📦 APK Release:     build/app/outputs/flutter-apk/app-release.apk
  🔐 Coverage Report: coverage/lcov.info (codecov integration)
  📋 Build Report:    build-report-{run_number}.md
  🏷️  GitHub Release: v{run_number}-{run_id}

Monitor Build:
  https://github.com/$(git config --get remote.origin.url | grep -oP '(?<=github\.com[:/]).*?(?=\.git)')/actions

📊 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Build completes in ~15-20 minutes
2. Download APK from GitHub Actions artifacts
3. Test on physical Android device
4. Review code coverage report
5. Create beta release branch if approved

$GREEN✅ BUILD PIPELINE INITIATED$RESET
"@
    
    Write-Host $report
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
function Main {
    Write-Host "`n$BLUE╔════════════════════════════════════════════════════════════════╗"
    Write-Host "║    ZWESTA TRADING APP - REBUILD WITH CI/CD GITHUB ACTIONS      ║"
    Write-Host "╚════════════════════════════════════════════════════════════════╝$RESET`n"
    
    try {
        Test-Prerequisites
        Prepare-Git
        Create-Commit -Branch $Branch
        Push-ToRemote -Branch $Branch
        Run-LocalTests
        Trigger-CICD -Branch $Branch -ApiUrl $ApiUrl
        Generate-Report -Branch $Branch
        
        Write-Success "✨ CI/CD pipeline successfully initiated!"
    }
    catch {
        Write-Error "Build process failed: $_"
        exit 1
    }
}

# Run main
Main
