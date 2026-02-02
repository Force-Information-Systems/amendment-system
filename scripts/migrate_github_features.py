"""
Migration script to add GitHub Issues features:
- Add parent_comment_id to qa_comments (threading)
- Create comment_mentions table
- Create amendment_watchers table
- Create comment_reactions table
"""

import sqlite3
import os
from datetime import datetime


def migrate():
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'amendment_system.db')

    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        return

    # Create backup
    backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    print(f"Creating backup at {backup_path}")
    import shutil
    shutil.copy2(db_path, backup_path)
    print("Backup created successfully!")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Add parent_comment_id to qa_comments (if not exists)
        print("\n1. Adding parent_comment_id to qa_comments table...")
        try:
            cursor.execute("""
                ALTER TABLE qa_comments
                ADD COLUMN parent_comment_id INTEGER REFERENCES qa_comments(comment_id) ON DELETE CASCADE
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_comments_parent ON qa_comments(parent_comment_id)")
            print("   ✓ Added parent_comment_id column and index")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   - Column already exists, skipping")
            else:
                raise

        # 2. Create comment_mentions table
        print("\n2. Creating comment_mentions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comment_mentions (
                mention_id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id INTEGER NOT NULL REFERENCES qa_comments(comment_id) ON DELETE CASCADE,
                mentioned_employee_id INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
                mentioned_by_employee_id INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
                created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_notified BOOLEAN DEFAULT 0,
                FOREIGN KEY (comment_id) REFERENCES qa_comments(comment_id) ON DELETE CASCADE,
                FOREIGN KEY (mentioned_employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
                FOREIGN KEY (mentioned_by_employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comment_mentions_comment ON comment_mentions(comment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comment_mentions_employee ON comment_mentions(mentioned_employee_id)")
        print("   ✓ Created comment_mentions table with indexes")

        # 3. Create amendment_watchers table
        print("\n3. Creating amendment_watchers table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS amendment_watchers (
                watcher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                amendment_id INTEGER NOT NULL REFERENCES amendments(amendment_id) ON DELETE CASCADE,
                employee_id INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
                watch_reason VARCHAR(50) DEFAULT 'Manual',
                is_watching BOOLEAN DEFAULT 1,
                created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notify_comments BOOLEAN DEFAULT 1,
                notify_status_changes BOOLEAN DEFAULT 1,
                notify_mentions BOOLEAN DEFAULT 1,
                UNIQUE(amendment_id, employee_id),
                FOREIGN KEY (amendment_id) REFERENCES amendments(amendment_id) ON DELETE CASCADE,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_amendment_watchers_amendment ON amendment_watchers(amendment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_amendment_watchers_employee ON amendment_watchers(employee_id)")
        print("   ✓ Created amendment_watchers table with indexes")

        # 4. Create comment_reactions table
        print("\n4. Creating comment_reactions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comment_reactions (
                reaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id INTEGER NOT NULL REFERENCES qa_comments(comment_id) ON DELETE CASCADE,
                employee_id INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
                emoji VARCHAR(10) NOT NULL,
                created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(comment_id, employee_id, emoji),
                FOREIGN KEY (comment_id) REFERENCES qa_comments(comment_id) ON DELETE CASCADE,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comment_reactions_comment ON comment_reactions(comment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comment_reactions_employee ON comment_reactions(employee_id)")
        print("   ✓ Created comment_reactions table with indexes")

        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"\n   Database backup: {backup_path}")
        print("\n   Changes:")
        print("   - Added parent_comment_id to qa_comments (threading support)")
        print("   - Created comment_mentions table (@ mentions)")
        print("   - Created amendment_watchers table (watch/subscribe)")
        print("   - Created comment_reactions table (emoji reactions)")

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("GitHub Issues Features - Database Migration")
    print("=" * 60)
    migrate()
