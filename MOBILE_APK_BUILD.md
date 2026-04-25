# Zwesta Trading System - Mobile APK Build Guide

## Prerequisites

### Required Tools
1. **Flutter SDK** - Latest stable channel
2. **Android SDK** - API level 21+
3. **Java Development Kit (JDK)** - Version 11+
4. **Android Studio** - Recommended (includes emulator)

### Check Installation
```bash
flutter --version
flutter doctor

# Should show: Android toolchain, Android SDK, Java, all OK
```

---

## Step 1: Prepare Signing Configuration

### 1.1 Create Signing Key
```bash
cd android

# Generate keystore (one-time)
keytool -genkey -v -keystore app-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10950 \
  -alias zwesta-app

# When prompted:
# Keystore password: (create strong password)
# First and last name: Zwesta Trading
# Organizational unit: Development
# Country code: US (or your country)

# Keep this file safe - it's needed for all future builds!
```

### 1.2 Create Key Configuration File
Create: `android/key.properties`
```properties
storePassword=your_keystore_password
keyPassword=your_key_password
keyAlias=zwesta-app
storeFile=app-release-key.jks
```

⚠️ **IMPORTANT**: Add `key.properties` to `.gitignore` - NEVER commit this file!

---

## Step 2: Configure Android Build

### 2.1 Update build.gradle
Edit: `android/app/build.gradle`

Find the `android` block and add signing configuration:
```gradle
signingConfigs {
    release {
        keyAlias keystoreProperties['keyAlias']
        keyPassword keystoreProperties['keyPassword']
        storeFile file(keystoreProperties['storeFile'])
        storePassword keystoreProperties['storePassword']
    }
}

buildTypes {
    release {
        signingConfig signingConfigs.release
        shrinkResources true
        minifyEnabled true
        proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
    }
}
```

### 2.2 Configure Package Name (Optional)
Edit: `android/app/src/main/AndroidManifest.xml`
```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.zwestatrading.app">  <!-- Change this -->
```

Or use:
```bash
# Change package name throughout project
flutter pub run rename --appname "Zwesta Trading" --bundleId com.zwestatrading.app
```

---

## Step 3: Update Permissions

Edit: `android/app/src/main/AndroidManifest.xml`

Add required permissions:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

---

## Step 4: Configure API Endpoint for Production

Edit: `lib/utils/environment_config.dart`

Update for Android production:
```dart
// For production APK
static const String _prodApiUrl = 'https://api.zwesta.com';

// Or if using VPS IP:
static const String _prodApiUrl = 'https://38.247.146.198:9000';
```

---

## Step 5: Build Release APK

### 5.1 Clean Build
```bash
flutter clean
flutter pub get
```

### 5.2 Build APK
```bash
# Standard APK (larger, supports all architectures)
flutter build apk --release

# Or split APK per architecture (smaller downloads)
flutter build apk --release --split-per-abi

# Output: build/app/outputs/apk/release/
```

### 5.3 Build App Bundle (Recommended for Play Store)
```bash
flutter build appbundle --release

# Output: build/app/outputs/bundle/release/
```

---

## Step 6: Test on Device/Emulator

### 6.1 Connect Device
```bash
# Enable USB Debugging on Android device
# Connect via USB or run emulator

# List connected devices
flutter devices

# Install APK on device
flutter install build/app/outputs/apk/release/app-release.apk

# Or using adb:
adb install -r build/app/outputs/apk/release/app-release.apk
```

### 6.2 Test on Emulator
```bash
# Create emulator if needed
flutter emulators --create --name pixel

# Start emulator
flutter emulators --launch pixel

# Build and run
flutter run --release
```

---

## Step 7: Android App Bundle for Play Store

### 7.1 Build Bundle
```bash
flutter build appbundle --release

# Output: build/app/outputs/bundle/release/app-release.aab
```

### 7.2 Test Bundle Locally
```bash
# Download bundletool from Google
wget https://developer.android.com/studio/command-line/bundletool

# Generate APKs from bundle
bundletool build-apks \
  --bundle=build/app/outputs/bundle/release/app-release.aab \
  --output=app.apks \
  --mode=universal \
  --ks=android/app-release-key.jks \
  --ks-key-alias=zwesta-app \
  --ks-pass=pass:your_password

# Install on device
bundletool install-apks --apks=app.apks
```

---

## Step 8: Create Release Notes

Create: `RELEASE_NOTES_ANDROID.md`
```markdown
# Zwesta Trading System - Mobile Release

## Version 1.0.0

### Features
- Multi-broker support (MT5, IB)
- Live trading dashboard
- Account management
- Trade history and reports
- Position tracking
- Real-time P&L

### Improvements
- Optimized for mobile performance
- Improved UI responsiveness
- Enhanced security
- Better error handling

### Bug Fixes
- Fixed API connection timeout
- Resolved trade data loading issue
- Improved offline handling

### Supported OS
- Android 5.0 (API 21) and above

### Installation
1. Download APK or install from Play Store
2. Grant required permissions
3. Enter your broker credentials
4. Start trading!
```

---

## Step 9: Play Store Submission

### 9.1 Create Google Play Developer Account
- Visit: https://play.google.com/apps/publish
- Pay one-time fee: $25 USD
- Complete registration

### 9.2 Create App Listing
1. Click "Create App"
2. Fill in app details:
   - App name: "Zwesta Trading"
   - Default language: English
   - App type: Finance/Tools
   
3. Add screenshots (minimum 2):
   - 1080 x 1920 px recommended
   - Upload 4-8 screenshots

4. Write description:
   ```
   Zwesta Trading - professional multi-broker trading platform on your mobile device.
   
   Connect to MetaTrader 5, Interactive Brokers and more.
   Monitor your positions, place trades, and analyze performance in real-time.
   ```

5. Add icon (512x512 PNG)
6. Add feature graphic (1024x500 PNG)

### 9.3 Upload APK/AAB
1. Go to "Release Management"
2. Click "Releases"
3. Select "Production"
4. Upload `app-release.aab`
5. Add release notes
6. Review and submit

### 9.4 Play Store Review
- Review process: 24-48 hours typically
- Check email for approval or rejection
- Address any issues if rejected

---

## Distribution Methods

### Method 1: Direct APK Distribution
```bash
# Copy APK to distribution
cp build/app/outputs/apk/release/app-release.apk ~/Downloads/zwesta-trading.apk

# Share via email, cloud storage, or your website
# Users: Install via "Install Unknown Apps" permission
```

### Method 2: Google Play Store
- See section 9 above

### Method 3: Enterprise Distribution (Beta)
```bash
# Use Firebase App Distribution
firebase appdistribution:distribute build/app/outputs/apk/release/app-release.apk \
  --app 1:234567890:android:abcdef123456

# Testers can install via email link
```

### Method 4: GitHub Releases
```bash
# Tag release
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Create release on GitHub with APK attached
# Users can download from GitHub releases page
```

---

## Build Optimization

### Reduce APK Size
```bash
# Build with split per ABI (smaller APKs)
flutter build apk --release --split-per-abi

# Results:
# - armeabi-v7a: ~15MB
# - arm64-v8a: ~17MB
# - x86: ~18MB
# (vs ~35MB for universal)
```

### Shrink Resources
Already configured in build.gradle:
```gradle
shrinkResources true
minifyEnabled true
```

### ProGuard Rules
Edit: `android/app/proguard-rules.pro`
```
-obfuscationdictionary unicode_dictionary.txt
-classobfuscationdictionary unicode_dictionary.txt
-packageobfuscationdictionary unicode_dictionary.txt

# Keep API clients
-keep class com.example.** { *; }
```

---

## Troubleshooting

### Issue: "Key was created with errors"
```bash
# Delete old key and recreate
rm android/app-release-key.jks
keytool -genkey -v -keystore android/app-release-key.jks ...
```

### Issue: "Gradle build failed"
```bash
# Clean and rebuild
flutter clean
cd android && ./gradlew clean
cd ..
flutter pub get
flutter build apk --release
```

### Issue: "API connection timeout on device"
Edit: `lib/utils/environment_config.dart`
```dart
// Use VPS IP instead of localhost
static const String _prodApiUrl = 'http://38.247.146.198:9000';
```

### Issue: "App crashes on permissions"
Add to `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

Request at runtime:
```dart
import 'package:permission_handler/permission_handler.dart';

Future<void> requestPermissions() async {
  await Permission.camera.request();
  await Permission.location.request();
  await Permission.storage.request();
}
```

---

## Testing Checklist

- [ ] API connection working
- [ ] Login screen displays correctly
- [ ] Dashboard loads trades
- [ ] Can view account info
- [ ] Can view positions
- [ ] Can place demo trade
- [ ] Can close position
- [ ] Reports load correctly
- [ ] No crashes on navigation
- [ ] Handles offline state
- [ ] Permissions working
- [ ] APK installs on device
- [ ] APK installs on emulator

---

## Commands Reference

```bash
# Check setup
flutter doctor

# Clean build
flutter clean

# Get dependencies
flutter pub get

# Build APK
flutter build apk --release

# Build App Bundle
flutter build appbundle --release

# Test on device
flutter run --release

# View connected devices
flutter devices

# Install on device
adb install -r build/app/outputs/apk/release/app-release.apk

# View logs
flutter logs

# Build with verbose output
flutter build apk --release -v
```

---

## Signing Configuration Summary

```
Keystore File: android/app-release-key.jks
Key Alias: zwesta-app
Configuration: android/key.properties (DO NOT COMMIT!)
Build Type: release
Output: build/app/outputs/apk/release/app-release.apk
Bundle: build/app/outputs/bundle/release/app-release.aab
```

---

## Next Steps

1. ✅ Build release APK
2. ✅ Test on device/emulator
3. ✅ Submit to Play Store (optional)
4. ✅ Distribute via enterprise method
5. ✅ Monitor crash reports
6. ✅ Gather user feedback

---

**APK Build Complete!** Your mobile app is ready for distribution.
