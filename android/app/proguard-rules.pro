# Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }
-keep class io.flutter.embedding.** { *; }
-keep class io.flutter.embedding.engine.** { *; }
-keep class io.flutter.embedding.android.** { *; }
-keep class io.flutter.plugin.common.** { *; }
-keep class io.flutter.plugin.platform.** { *; }
-dontwarn io.flutter.embedding.**

# Generated plugin registrants used by Flutter embedding v2
-keep class io.flutter.plugins.GeneratedPluginRegistrant { *; }

# Keep Flutter local notifications
-keep class com.dexterous.** { *; }

# Keep WebSocket / JSON model classes used by provider packages
-keep class com.google.gson.** { *; }
-keepattributes Signature
-keepattributes *Annotation*
-keepattributes *JavascriptInterface*

# Keep app entry points and any classes referenced from Dart (JNI/reflection)
-keep class com.zwesta.trading.** { *; }

# OkHttp (used by http package internally)
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn javax.annotation.**
-dontwarn org.conscrypt.**
-keepnames class okhttp3.internal.publicsuffix.PublicSuffixDatabase

# Kotlin metadata / coroutines
-keepattributes *Annotation*
-dontwarn kotlin.**
-dontwarn kotlinx.coroutines.**

# Biometric / Security extras
-dontwarn androidx.biometric.**
-dontwarn androidx.security.**
-keep class androidx.biometric.** { *; }
-keep class androidx.security.** { *; }

# Model JSON annotations / reflection used by Dart serializers
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}

# Prevent stripping Dart-generated RegisterMappers / Flutter loader
-keepclassmembers class * {
    public static *** access$*(...);
}
