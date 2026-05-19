#!/usr/bin/env python3
"""
Database Recovery Script for Zwesta Trading Backend
Restores the most recent backup to fix corrupted database
"""

import sqlite3
import shutil
import os
import gzip
from datetime import datetime
from pathlib import Path

def restore_latest_backup():
    """Restore the most recent backup to fix corrupted database"""

    # VPS database path
    db_path = r'C:\backend\zwesta_trading.db'

    # Local backup directory
    backup_dir = Path(r'C:\zwesta-trader\backups')

    print("="*60)
    print("ZWESTA DATABASE RECOVERY")
    print("="*60)

    # Find the most recent backup
    backup_files = sorted(backup_dir.glob('backup_*.db.gz'), reverse=True)

    if not backup_files:
        print("❌ No backup files found!")
        return False

    latest_backup = backup_files[0]
    print(f"📁 Found latest backup: {latest_backup.name}")
    print(f"📅 Created: {datetime.fromtimestamp(latest_backup.stat().st_mtime)}")
    print(f"📏 Size: {latest_backup.stat().st_size / (1024*1024):.2f} MB")

    # Create safety backup of corrupted database
    if os.path.exists(db_path):
        safety_backup = f"{db_path}.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"🛡️ Creating safety backup of corrupted database: {safety_backup}")
        shutil.copy2(db_path, safety_backup)

    try:
        # Restore from backup
        print(f"🔄 Restoring from backup: {latest_backup.name}")
        with gzip.open(latest_backup, 'rb') as f_in:
            with open(db_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print("✅ Database restored successfully!")

        # Verify the restored database
        print("🔍 Verifying restored database...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check main tables
        tables_to_check = ['users', 'user_bots', 'broker_credentials', 'trades']
        for table in tables_to_check:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count} records")
            except sqlite3.Error as e:
                print(f"   ⚠️ {table}: Error - {e}")

        conn.close()
        print("✅ Database verification complete!")
        return True

    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

if __name__ == '__main__':
    success = restore_latest_backup()
    if success:
        print("\n🎉 Database recovery successful!")
        print("🚀 You can now restart the backend server.")
    else:
        print("\n💥 Database recovery failed!")
        print("📞 Contact support for manual recovery.")