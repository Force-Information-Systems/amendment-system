#!/usr/bin/env python3
"""
Database migration script to add authentication columns to employees table.

This script adds the following columns to the employees table:
- role: User role (Admin or User), defaults to 'User'
- password_hash: Hashed password for local authentication (nullable for AD-only users)
- last_login: Timestamp of last successful login

Also creates indexes on email and windows_login columns for performance.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path(__file__).parent.parent / 'backend' / 'amendment_system.db'


def create_backup():
    """Create a backup of the database before migration."""
    backup_path = DB_PATH.parent / f"amendment_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✓ Database backup created: {backup_path.name}")
        return True
    except Exception as e:
        print(f"✗ Failed to create backup: {e}")
        return False


def run_migration():
    """Run the database migration to add authentication columns."""
    if not DB_PATH.exists():
        print(f"✗ Database not found at: {DB_PATH}")
        print("  Please ensure the database exists before running migration.")
        return False

    print(f"Starting migration on database: {DB_PATH}")
    print()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(employees)")
        columns = {row[1] for row in cursor.fetchall()}

        migrations_needed = []
        if 'role' not in columns:
            migrations_needed.append('role')
        if 'password_hash' not in columns:
            migrations_needed.append('password_hash')
        if 'last_login' not in columns:
            migrations_needed.append('last_login')

        if not migrations_needed:
            print("✓ All authentication columns already exist. No migration needed.")
            conn.close()
            return True

        print(f"Adding columns: {', '.join(migrations_needed)}")

        # Add new columns
        if 'role' in migrations_needed:
            cursor.execute('ALTER TABLE employees ADD COLUMN role TEXT DEFAULT "User" NOT NULL')
            print("  ✓ Added 'role' column")

        if 'password_hash' in migrations_needed:
            cursor.execute('ALTER TABLE employees ADD COLUMN password_hash TEXT')
            print("  ✓ Added 'password_hash' column")

        if 'last_login' in migrations_needed:
            cursor.execute('ALTER TABLE employees ADD COLUMN last_login DATETIME')
            print("  ✓ Added 'last_login' column")

        # Create indexes if they don't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}

        if 'idx_employee_email' not in indexes:
            cursor.execute('CREATE INDEX idx_employee_email ON employees(email)')
            print("  ✓ Created index on 'email' column")

        if 'idx_employee_windows_login' not in indexes:
            cursor.execute('CREATE UNIQUE INDEX idx_employee_windows_login ON employees(windows_login) WHERE windows_login IS NOT NULL')
            print("  ✓ Created unique index on 'windows_login' column")

        conn.commit()
        print()
        print("✓ Migration completed successfully!")
        print()
        print("Next steps:")
        print("  1. Run: python3 scripts/create_admin.py")
        print("  2. Start the server: cd backend && uvicorn app.main:app --reload")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main migration function."""
    print("=" * 60)
    print("Amendment System - Authentication Migration")
    print("=" * 60)
    print()

    # Create backup
    if not create_backup():
        response = input("\nBackup failed. Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return 1

    print()

    # Run migration
    if run_migration():
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
