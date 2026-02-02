#!/usr/bin/env python3
"""
Database migration script to add comprehensive QA system tables and fields.

This script adds:
- 5 new tables: qa_test_cases, qa_test_executions, qa_defects, qa_history, qa_notifications
- New columns to amendments table: qa_due_date, qa_sla_hours
- Indexes for performance optimization

Part of the comprehensive QA system implementation.
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
    """Run the database migration to add QA system tables."""
    if not DB_PATH.exists():
        print(f"✗ Database not found at: {DB_PATH}")
        print("  Please ensure the database exists before running migration.")
        return False

    print(f"Starting QA system migration on database: {DB_PATH}")
    print()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        migrations_run = []

        # ============================================================
        # 1. Create qa_test_cases table
        # ============================================================
        if 'qa_test_cases' not in existing_tables:
            cursor.execute('''
                CREATE TABLE qa_test_cases (
                    test_case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_case_number TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT,
                    test_type TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'Medium',

                    -- Test details
                    preconditions TEXT,
                    test_steps TEXT,
                    expected_results TEXT,

                    -- Classification
                    application_id INTEGER,
                    component TEXT,
                    tags TEXT,

                    -- Status
                    is_active INTEGER DEFAULT 1,
                    is_automated INTEGER DEFAULT 0,
                    automation_script TEXT,

                    -- Audit fields
                    created_by TEXT,
                    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
                    modified_by TEXT,
                    modified_on DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (application_id) REFERENCES applications(application_id)
                )
            ''')

            # Create indexes for qa_test_cases
            cursor.execute('CREATE INDEX idx_test_case_number ON qa_test_cases(test_case_number)')
            cursor.execute('CREATE INDEX idx_test_case_type ON qa_test_cases(test_type)')
            cursor.execute('CREATE INDEX idx_test_case_priority ON qa_test_cases(priority)')
            cursor.execute('CREATE INDEX idx_test_case_application ON qa_test_cases(application_id)')
            cursor.execute('CREATE INDEX idx_test_case_active ON qa_test_cases(is_active)')

            migrations_run.append("qa_test_cases table")
            print("  ✓ Created qa_test_cases table with indexes")

        # ============================================================
        # 2. Create qa_test_executions table
        # ============================================================
        if 'qa_test_executions' not in existing_tables:
            cursor.execute('''
                CREATE TABLE qa_test_executions (
                    execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amendment_id INTEGER NOT NULL,
                    test_case_id INTEGER NOT NULL,
                    executed_by_id INTEGER,

                    -- Execution details
                    execution_status TEXT NOT NULL DEFAULT 'Not Run',
                    executed_on DATETIME,
                    duration_minutes INTEGER,

                    -- Results
                    actual_results TEXT,
                    notes TEXT,
                    attachments TEXT,

                    -- Environment
                    test_environment TEXT,
                    build_version TEXT,

                    -- Audit fields
                    created_by TEXT,
                    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
                    modified_by TEXT,
                    modified_on DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (amendment_id) REFERENCES amendments(amendment_id) ON DELETE CASCADE,
                    FOREIGN KEY (test_case_id) REFERENCES qa_test_cases(test_case_id),
                    FOREIGN KEY (executed_by_id) REFERENCES employees(employee_id)
                )
            ''')

            # Create indexes for qa_test_executions
            cursor.execute('CREATE INDEX idx_test_execution_amendment ON qa_test_executions(amendment_id)')
            cursor.execute('CREATE INDEX idx_test_execution_test_case ON qa_test_executions(test_case_id)')
            cursor.execute('CREATE INDEX idx_test_execution_status ON qa_test_executions(execution_status)')
            cursor.execute('CREATE INDEX idx_test_execution_executed_by ON qa_test_executions(executed_by_id)')
            cursor.execute('CREATE INDEX idx_test_execution_date ON qa_test_executions(executed_on)')

            migrations_run.append("qa_test_executions table")
            print("  ✓ Created qa_test_executions table with indexes")

        # ============================================================
        # 3. Create qa_defects table
        # ============================================================
        if 'qa_defects' not in existing_tables:
            cursor.execute('''
                CREATE TABLE qa_defects (
                    defect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    defect_number TEXT NOT NULL UNIQUE,
                    amendment_id INTEGER NOT NULL,
                    test_execution_id INTEGER,

                    -- Defect details
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT NOT NULL DEFAULT 'Medium',
                    status TEXT NOT NULL DEFAULT 'New',

                    -- Reproduction
                    steps_to_reproduce TEXT,
                    actual_behavior TEXT,
                    expected_behavior TEXT,

                    -- Assignment
                    reported_by_id INTEGER,
                    assigned_to_id INTEGER,

                    -- Resolution
                    resolution TEXT,
                    root_cause TEXT,
                    fixed_in_version TEXT,

                    -- Dates
                    reported_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    assigned_date DATETIME,
                    resolved_date DATETIME,
                    closed_date DATETIME,

                    -- Audit fields
                    created_by TEXT,
                    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
                    modified_by TEXT,
                    modified_on DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (amendment_id) REFERENCES amendments(amendment_id) ON DELETE CASCADE,
                    FOREIGN KEY (test_execution_id) REFERENCES qa_test_executions(execution_id),
                    FOREIGN KEY (reported_by_id) REFERENCES employees(employee_id),
                    FOREIGN KEY (assigned_to_id) REFERENCES employees(employee_id)
                )
            ''')

            # Create indexes for qa_defects
            cursor.execute('CREATE INDEX idx_defect_number ON qa_defects(defect_number)')
            cursor.execute('CREATE INDEX idx_defect_amendment ON qa_defects(amendment_id)')
            cursor.execute('CREATE INDEX idx_defect_test_execution ON qa_defects(test_execution_id)')
            cursor.execute('CREATE INDEX idx_defect_status ON qa_defects(status)')
            cursor.execute('CREATE INDEX idx_defect_severity ON qa_defects(severity)')
            cursor.execute('CREATE INDEX idx_defect_assigned_to ON qa_defects(assigned_to_id)')
            cursor.execute('CREATE INDEX idx_defect_reported_by ON qa_defects(reported_by_id)')

            migrations_run.append("qa_defects table")
            print("  ✓ Created qa_defects table with indexes")

        # ============================================================
        # 4. Create qa_history table
        # ============================================================
        if 'qa_history' not in existing_tables:
            cursor.execute('''
                CREATE TABLE qa_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amendment_id INTEGER NOT NULL,
                    action TEXT NOT NULL,

                    -- Change details
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    comment TEXT,

                    -- Audit
                    changed_by_id INTEGER,
                    changed_on DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (amendment_id) REFERENCES amendments(amendment_id) ON DELETE CASCADE,
                    FOREIGN KEY (changed_by_id) REFERENCES employees(employee_id)
                )
            ''')

            # Create indexes for qa_history
            cursor.execute('CREATE INDEX idx_qa_history_amendment ON qa_history(amendment_id)')
            cursor.execute('CREATE INDEX idx_qa_history_action ON qa_history(action)')
            cursor.execute('CREATE INDEX idx_qa_history_changed_by ON qa_history(changed_by_id)')
            cursor.execute('CREATE INDEX idx_qa_history_changed_on ON qa_history(changed_on)')

            migrations_run.append("qa_history table")
            print("  ✓ Created qa_history table with indexes")

        # ============================================================
        # 5. Create qa_notifications table
        # ============================================================
        if 'qa_notifications' not in existing_tables:
            cursor.execute('''
                CREATE TABLE qa_notifications (
                    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    notification_type TEXT NOT NULL,

                    -- Content
                    title TEXT NOT NULL,
                    message TEXT,

                    -- Links
                    amendment_id INTEGER,
                    defect_id INTEGER,

                    -- Status
                    is_read INTEGER DEFAULT 0,
                    is_email_sent INTEGER DEFAULT 0,
                    read_on DATETIME,

                    -- Audit
                    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
                    FOREIGN KEY (amendment_id) REFERENCES amendments(amendment_id) ON DELETE CASCADE,
                    FOREIGN KEY (defect_id) REFERENCES qa_defects(defect_id) ON DELETE CASCADE
                )
            ''')

            # Create indexes for qa_notifications
            cursor.execute('CREATE INDEX idx_notification_employee ON qa_notifications(employee_id)')
            cursor.execute('CREATE INDEX idx_notification_type ON qa_notifications(notification_type)')
            cursor.execute('CREATE INDEX idx_notification_amendment ON qa_notifications(amendment_id)')
            cursor.execute('CREATE INDEX idx_notification_defect ON qa_notifications(defect_id)')
            cursor.execute('CREATE INDEX idx_notification_read ON qa_notifications(is_read)')
            cursor.execute('CREATE INDEX idx_notification_created ON qa_notifications(created_on)')

            migrations_run.append("qa_notifications table")
            print("  ✓ Created qa_notifications table with indexes")

        # ============================================================
        # 6. Add new columns to amendments table
        # ============================================================
        cursor.execute("PRAGMA table_info(amendments)")
        amendment_columns = {row[1] for row in cursor.fetchall()}

        if 'qa_due_date' not in amendment_columns:
            cursor.execute('ALTER TABLE amendments ADD COLUMN qa_due_date DATETIME')
            migrations_run.append("qa_due_date column")
            print("  ✓ Added qa_due_date column to amendments")

        if 'qa_sla_hours' not in amendment_columns:
            cursor.execute('ALTER TABLE amendments ADD COLUMN qa_sla_hours INTEGER DEFAULT 48')
            migrations_run.append("qa_sla_hours column")
            print("  ✓ Added qa_sla_hours column to amendments (default 48 hours)")

        # Commit all changes
        conn.commit()

        print()
        if migrations_run:
            print("✓ QA System migration completed successfully!")
            print()
            print("Summary of changes:")
            for item in migrations_run:
                print(f"  • {item}")
            print()
            print("Next steps:")
            print("  1. Update backend/app/models.py with new model classes")
            print("  2. Add Pydantic schemas to backend/app/schemas.py")
            print("  3. Add CRUD functions to backend/app/crud.py")
            print("  4. Add API endpoints to backend/app/main.py")
            print("  5. Restart the backend server")
        else:
            print("✓ All QA system tables already exist. No migration needed.")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def main():
    """Main migration function."""
    print("=" * 60)
    print("Amendment System - Comprehensive QA System Migration")
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
