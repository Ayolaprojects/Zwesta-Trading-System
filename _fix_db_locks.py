"""
Fix database locking issues by enabling WAL mode and optimizing SQLite settings
"""
import sqlite3
import os

DB_PATH = r'C:\backend\zwesta_trading.db'

print(f"🔧 Fixing database locks: {DB_PATH}")

# Connect with extended timeout
conn = sqlite3.connect(DB_PATH, timeout=60.0, check_same_thread=False)
cursor = conn.cursor()

print("\n📊 Current database settings:")
try:
    result = cursor.execute('PRAGMA journal_mode').fetchone()
    print(f"  Journal mode: {result[0] if result else 'unknown'}")
except Exception as e:
    print(f"  Error checking journal_mode: {e}")

try:
    result = cursor.execute('PRAGMA synchronous').fetchone()
    print(f"  Synchronous: {result[0] if result else 'unknown'}")
except Exception as e:
    print(f"  Error checking synchronous: {e}")

try:
    result = cursor.execute('PRAGMA busy_timeout').fetchone()
    print(f"  Busy timeout: {result[0]}ms" if result else "  Busy timeout: unknown")
except Exception as e:
    print(f"  Error checking busy_timeout: {e}")

print("\n🔄 Applying fixes...")

# Enable WAL mode for concurrent access
print("  Setting journal_mode=WAL...")
result = cursor.execute('PRAGMA journal_mode=WAL').fetchone()
print(f"    ✓ Journal mode: {result[0]}")

# Set synchronous to NORMAL for better performance with WAL
print("  Setting synchronous=NORMAL...")
cursor.execute('PRAGMA synchronous=NORMAL')
print("    ✓ Synchronous set to NORMAL")

# Increase busy timeout to 2 minutes
print("  Setting busy_timeout=120000ms (2 minutes)...")
cursor.execute('PRAGMA busy_timeout=120000')
print("    ✓ Busy timeout set")

# Increase cache size
print("  Setting cache_size=-64000 (64MB)...")
cursor.execute('PRAGMA cache_size=-64000')
print("    ✓ Cache size set")

# Enable memory-mapped I/O for better performance
print("  Setting mmap_size=268435456 (256MB)...")
try:
    cursor.execute('PRAGMA mmap_size=268435456')
    print("    ✓ Memory-mapped I/O enabled")
except Exception as e:
    print(f"    ⚠️ Could not set mmap_size: {e}")

conn.commit()

print("\n📊 Verified new settings:")
result = cursor.execute('PRAGMA journal_mode').fetchone()
print(f"  Journal mode: {result[0]}")
result = cursor.execute('PRAGMA synchronous').fetchone()
print(f"  Synchronous: {result[0]}")
result = cursor.execute('PRAGMA busy_timeout').fetchone()
print(f"  Busy timeout: {result[0]}ms")

conn.close()

print("\n✅ Database optimized for concurrent access!")
print("   • WAL mode enabled (allows concurrent reads during writes)")
print("   • Extended busy timeout (handles write contention)")
print("   • Optimized cache and synchronous settings")
print("\nRestart the backend to apply changes.")
