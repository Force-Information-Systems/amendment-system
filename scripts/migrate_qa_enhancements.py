#!/usr/bin/env python3
"""
Database migration script to add QA enhancement fields and qa_comments table.

This script adds:
- New column to amendments table: version (for version grouping like "Centurion 7.5")
- New column to amendments table: qa_overall_result (for overall QA outcome)
- New table: qa_comments (for QA discussion threads)

Part of Phase 3.5 QA system enhancements.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path(__file__).parent.parent / 'backend' / 'amendment_system.db'


def create_backup():
    """Create a backup of the database before migration."""
    backup_path = DB_PATH.parent / f"amendment_system_backup_qa_enhancements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✓ Database backup created: {backup_path.name}")
        return True
    except Exception as e:
        print(f"✗ Failed to create backup: {e}")
        return False


def run_migration():
    """Run the database migration to add QA enhancement fields and qa_comments table."""
    if not DB_PATH.exists():
        print(f"✗ Database not found at: {DB_PATH}")
        print("  Please ensure the database exists before running migration.")
        return False

    print(f"Starting QA enhancements migration on database: {DB_PATH}")
    print()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        # Check existing columns in amendments table
        cursor.execute("PRAGMA table_info(amendments)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        migrations_run = []

        # ============================================================
        # 1. Add version column to amendments table
        # ============================================================
        if 'version' not in existing_columns:
            print("Adding 'version' column to amendments table...")
            cursor.execute('''
                ALTER TABLE amendments
                ADD COLUMN version TEXT
            ''')

            # Create index for version
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_amendment_version ON amendments(version)')

            migrations_run.append("Added 'version' column to amendments table")
            print("✓ Added 'version' column")
        else:
            print("⊘ 'version' column already exists in amendments table")

        # ============================================================
        # 2. Add qa_overall_result column to amendments table
        # ============================================================
        if 'qa_overall_result' not in existing_columns:
            print("Adding 'qa_overall_result' column to amendments table...")
            cursor.execute('''
                ALTER TABLE amendments
                ADD COLUMN qa_overall_result TEXT
            ''')

            migrations_run.append("Added 'qa_overall_result' column to amendments table")
            print("✓ Added 'qa_overall_result' column")
        else:
            print("⊘ 'qa_overall_result' column already exists in amendments table")

        # ============================================================
        # 3. Create qa_comments table
        # ============================================================
        if 'qa_comments' not in existing_tables:
            print("Creating 'qa_comments' table...")
            cursor.execute('''
                CREATE TABLE qa_comments (
                    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amendment_id INTEGER NOT NULL,
                    employee_id INTEGER NOT NULL,

                    -- Content
                    comment_text TEXT NOT NULL,
                    comment_type TEXT NOT NULL DEFAULT 'General',

                    -- Metadata
                    is_edited INTEGER DEFAULT 0,
                    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
                    modified_on DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (amendment_id) REFERENCES amendments(amendment_id) ON DELETE CASCADE,
                    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
                )
            ''')

            # Create indexes for qa_comments
            cursor.execute('CREATE INDEX idx_qa_comment_amendment ON qa_comments(amendment_id)')
            cursor.execute('CREATE INDEX idx_qa_comment_employee ON qa_comments(employee_id)')
            cursor.execute('CREATE INDEX idx_qa_comment_created ON qa_comments(created_on)')
            cursor.execute('CREATE INDEX idx_qa_comment_type ON qa_comments(comment_type)')

            migrations_run.append("Created qa_comments table with indexes")
            print("✓ Created 'qa_comments' table")
            print("✓ Created indexes for qa_comments")
        else:
            print("⊘ 'qa_comments' table already exists")

        # Commit all changes
        conn.commit()

        print()
        print("=" * 60)
        print("Migration Summary:")
        print("=" * 60)
        if migrations_run:
            for migration in migrations_run:
                print(f"✓ {migration}")
            print()
            print(f"✓ Successfully applied {len(migrations_run)} migration(s)")
        else:
            print("⊘ No migrations needed - all enhancements already applied")
        print("=" * 60)

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"✗ SQLite error during migration: {e}")
        print(f"  Migration rolled back")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during migration: {e}")
        return False


def verify_migration():
    """Verify that the migration was successful."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print()
        print("Verifying migration...")
        print()

        # Check amendments table columns
        cursor.execute("PRAGMA table_info(amendments)")
        columns = {row[1] for row in cursor.fetchall()}

        # Verify version column
        if 'version' in columns:
            print("✓ 'version' column exists in amendments table")
        else:
            print("✗ 'version' column NOT FOUND in amendments table")
            return False

        # Verify qa_overall_result column
        if 'qa_overall_result' in columns:
            print("✓ 'qa_overall_result' column exists in amendments table")
        else:
            print("✗ 'qa_overall_result' column NOT FOUND in amendments table")
            return False

        # Check qa_comments table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qa_comments'")
        if cursor.fetchone():
            print("✓ 'qa_comments' table exists")

            # Check qa_comments structure
            cursor.execute("PRAGMA table_info(qa_comments)")
            qa_comments_columns = [row[1] for row in cursor.fetchall()]
            expected_columns = ['comment_id', 'amendment_id', 'employee_id', 'comment_text',
                              'comment_type', 'is_edited', 'created_on', 'modified_on']

            missing_columns = [col for col in expected_columns if col not in qa_comments_columns]
            if missing_columns:
                print(f"✗ Missing columns in qa_comments: {', '.join(missing_columns)}")
                return False
            else:
                print("✓ qa_comments table has all required columns")

            # Check indexes
            cursor.execute("PRAGMA index_list(qa_comments)")
            indexes = [row[1] for row in cursor.fetchall()]
            expected_indexes = ['idx_qa_comment_amendment', 'idx_qa_comment_employee',
                              'idx_qa_comment_created', 'idx_qa_comment_type']

            missing_indexes = [idx for idx in expected_indexes if idx not in indexes]
            if missing_indexes:
                print(f"⚠ Missing indexes: {', '.join(missing_indexes)}")
            else:
                print("✓ All qa_comments indexes exist")
        else:
            print("✗ 'qa_comments' table NOT FOUND")
            return False

        # Check version index
        cursor.execute("PRAGMA index_list(amendments)")
        indexes = [row[1] for row in cursor.fetchall()]
        if 'idx_amendment_version' in indexes:
            print("✓ 'idx_amendment_version' index exists")
        else:
            print("⚠ 'idx_amendment_version' index not found")

        print()
        print("=" * 60)
        print("✓ Migration verification PASSED")
        print("=" * 60)

        conn.close()
        return True

    except Exception as e:
        print(f"✗ Verification error: {e}")
        return False


def main():
    """Main migration execution."""
    print("=" * 60)
    print("QA System Enhancements Migration Script")
    print("=" * 60)
    print()

    # Create backup
    print("Step 1: Creating database backup...")
    if not create_backup():
        print("✗ Migration aborted - could not create backup")
        sys.exit(1)
    print()

    # Run migration
    print("Step 2: Running migration...")
    if not run_migration():
        print("✗ Migration failed")
        sys.exit(1)
    print()

    # Verify migration
    print("Step 3: Verifying migration...")
    if not verify_migration():
        print("✗ Verification failed")
        sys.exit(1)
    print()

    print("=" * 60)
    print("✓ QA ENHANCEMENTS MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Update Pydantic schemas for QAComment")
    print("2. Add CRUD functions for QA comments")
    print("3. Add API endpoints for QA comments")
    print("4. Implement frontend components")
    print()


if __name__ == "__main__":
    main()
