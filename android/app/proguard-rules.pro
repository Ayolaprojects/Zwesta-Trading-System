# Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }
-dontwarn io.flutter.embedding.**

# Keep Flutter local notifications
-keep class com.dexterous.** { *; }

# Keep WebSocket channel
-keep class com.google.gson.** { *; }
-keepattributes Signature
-keepattributes *Annotation*

# Keep app entry points
-keep class com.zwesta.trading.** { *; }

# OkHttp (used by http package internally)
-dontwarn okhttp3.**
-dontwarn okio.**
-keepnames class okhttp3.internal.publicsuffix.PublicSuffixDatabase

# Prevent stripping JSON model fields
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}
