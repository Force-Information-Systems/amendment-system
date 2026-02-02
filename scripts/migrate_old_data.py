#!/usr/bin/env python3
"""
Migration script to import amendments from old fis-amendments SQL Server database dump.

This script parses the script.sql file from the old system and imports amendments
into the new SQLite-based amendment tracking system.
"""

import re
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.database import SessionLocal, init_db
from backend.app import models, schemas, crud


def parse_sql_insert(insert_statement):
    """
    Parse a SQL INSERT statement and extract values.

    Returns a list of tuples, where each tuple represents a row of data.
    """
    # Extract values from INSERT ... VALUES (...), (...), ...
    values_pattern = r'VALUES\s*(.+?)$'
    values_match = re.search(values_pattern, insert_statement, re.IGNORECASE | re.DOTALL)

    if not values_match:
        return []

    values_text = values_match.group(1)

    # Parse values more carefully to handle nested parentheses
    rows = []
    current_row = []
    current_value = ''
    in_quote = False
    quote_char = None
    paren_depth = 0
    in_row = False

    for i, char in enumerate(values_text):
        # Handle quotes
        if char in ('"', "'") and (i == 0 or values_text[i-1] != '\\'):
            if not in_quote:
                in_quote = True
                quote_char = char
            elif char == quote_char:
                in_quote = False
                quote_char = None
            current_value += char
            continue

        # Inside quotes, just accumulate
        if in_quote:
            current_value += char
            continue

        # Handle parentheses outside of quotes
        if char == '(':
            paren_depth += 1
            if paren_depth == 1:
                in_row = True
                continue
            else:
                # Nested paren, part of value (like CAST(...))
                current_value += char
                continue

        if char == ')':
            paren_depth -= 1
            if paren_depth == 0:
                # End of row
                if current_value.strip():
                    current_row.append(current_value.strip())
                if current_row:
                    rows.append(current_row)
                current_row = []
                current_value = ''
                in_row = False
                continue
            else:
                # Nested paren closing
                current_value += char
                continue

        # Handle commas
        if char == ',' and paren_depth == 1:
            # Field separator within row
            if current_value.strip():
                current_row.append(current_value.strip())
            current_value = ''
            continue
        elif char == ',' and paren_depth == 0:
            # Row separator, skip
            continue

        # Accumulate other characters
        if paren_depth > 0:
            current_value += char

    return rows


def clean_sql_value(value):
    """Clean a SQL value (remove quotes, handle NULL, etc.)"""
    if not value:
        return None

    value = value.strip()

    if value.upper() == 'NULL':
        return None

    # Remove SQL Server N prefix for Unicode strings
    if value.upper().startswith("N'") or value.upper().startswith('N"'):
        value = value[1:]

    # Remove surrounding quotes
    if (value.startswith("'") and value.endswith("'")) or \
       (value.startswith('"') and value.endswith('"')):
        value = value[1:-1]

    # Unescape single quotes
    value = value.replace("''", "'")

    return value if value else None


def parse_date(date_str):
    """Parse a date string from SQL Server format."""
    if not date_str or date_str.upper() == 'NULL':
        return None

    # Extract date from CAST expressions like "CAST(N'2016-01-01T00:00:00.000' AS DateTime)"
    cast_match = re.search(r"CAST\(N?'([^']+)'", date_str, re.IGNORECASE)
    if cast_match:
        date_str = cast_match.group(1)

    # Try various date formats
    formats = [
        '%Y-%m-%dT%H:%M:%S.%f',  # ISO format with T
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def map_old_status_to_new(old_status):
    """Map old amendment status values to new enum values."""
    if not old_status:
        return 'Open'

    old_status = old_status.lower().strip()

    # Map old statuses to new ones
    status_map = {
        'open': 'Open',
        'in progress': 'In Progress',
        'in development': 'In Progress',
        'testing': 'Testing',
        'ready for qa': 'Testing',
        'completed': 'Completed',
        'applied to master': 'Completed',
        'released to customers': 'Deployed',
        'deployed': 'Deployed',
        'closed': 'Completed',
    }

    return status_map.get(old_status, 'Open')


def migrate_amendments(sql_file_path):
    """
    Migrate amendments from the SQL dump file.
    """
    print(f"Reading SQL file: {sql_file_path}")

    with open(sql_file_path, 'r', encoding='utf-16', errors='ignore') as f:
        sql_content = f.read()

    print(f"SQL file size: {len(sql_content)} characters")

    # Find all INSERT statements for Amendment table (singular, not plural!)
    # Pattern to match: INSERT [dbo].[Amendment] (...) VALUES (...)
    # Note: SQL Server exports use INSERT not INSERT INTO
    amendment_inserts = re.findall(
        r'INSERT\s+(?:INTO\s+)?\[dbo\]\.\[Amendment\]\s+.+?VALUES.+?\)',
        sql_content,
        re.IGNORECASE | re.DOTALL
    )

    print(f"Found {len(amendment_inserts)} INSERT statements for Amendments")

    if not amendment_inserts:
        print("No amendment data found in SQL file")
        # Let's try a simpler search
        print("\nSearching for any table inserts...")
        all_inserts = re.findall(
            r'INSERT\s+INTO\s+(\[?\w+\]?)',
            sql_content,
            re.IGNORECASE
        )
        table_names = set(all_inserts[:50])  # First 50 unique tables
        print(f"Found INSERT statements for tables: {table_names}")
        return 0

    db = SessionLocal()
    imported_count = 0

    skipped_count = 0
    try:
        for insert_stmt in amendment_inserts:
            rows = parse_sql_insert(insert_stmt)

            for row in rows:
                try:
                    # Skip rows with too few columns (probably AmendmentApplication table)
                    if len(row) < 15:
                        skipped_count += 1
                        continue

                    # Map SQL Server columns to our schema
                    # Based on actual SQL dump column order:
                    # 0: Amendment Id, 1: Amendment Type, 2: Amendment Reference,
                    # 3: Date Reported, 4: Description, 5: Amendment Status Id,
                    # 6: Amendment Status, 7: Force, 8: Reported By,
                    # 9: Application, 10: Version, 11: Assigned To,
                    # 12: Applied Version, 13: Priority, 14: Notes,
                    # 15: Created By, 16: Created On, 17: Modified By,
                    # 18: Modified On, 19: Database Changes, 20: DB Upgrade Changes,
                    # 21: Development Status Id, 22: Release Notes

                    amendment_data = schemas.AmendmentCreate(
                        amendment_type=clean_sql_value(row[1]) or 'Fault',
                        description=clean_sql_value(row[4]) or 'No description',
                        amendment_status=map_old_status_to_new(clean_sql_value(row[6])),
                        development_status='Not Started',  # Will be set separately if needed
                        priority=clean_sql_value(row[13]) or 'Medium',
                        force=clean_sql_value(row[7]),
                        application=clean_sql_value(row[9]),
                        notes=clean_sql_value(row[14]),
                        reported_by=clean_sql_value(row[8]),
                        assigned_to=clean_sql_value(row[11]),
                        date_reported=parse_date(clean_sql_value(row[3])),
                        database_changes=clean_sql_value(row[19]) == '1' if len(row) > 19 else False,
                        db_upgrade_changes=clean_sql_value(row[20]) == '1' if len(row) > 20 else False,
                        release_notes=clean_sql_value(row[22]) if len(row) > 22 else None,
                    )

                    # Create the amendment
                    created_by = clean_sql_value(row[15]) if len(row) > 15 else 'migration_script'

                    db_amendment = crud.create_amendment(db, amendment_data, created_by)

                    # Update the amendment reference to match the old system
                    if len(row) > 2 and row[2]:
                        old_reference = clean_sql_value(row[2])
                        if old_reference:
                            db_amendment.amendment_reference = old_reference

                    # Update QA fields if present
                    if len(row) > 23 and row[23]:  # QA Assigned Id
                        db_amendment.qa_assigned_id = clean_sql_value(row[23])
                    if len(row) > 24 and row[24]:  # QA Assigned Date
                        db_amendment.qa_assigned_date = parse_date(clean_sql_value(row[24]))
                    if len(row) > 25:  # QA Test Plan Check
                        db_amendment.qa_test_plan_check = clean_sql_value(row[25]) == '1'
                    if len(row) > 26:  # QA Test Release Notes Check
                        db_amendment.qa_test_release_notes_check = clean_sql_value(row[26]) == '1'
                    if len(row) > 27:  # QA Completed
                        db_amendment.qa_completed = clean_sql_value(row[27]) == '1'
                    if len(row) > 28 and row[28]:  # QA Signature
                        db_amendment.qa_signature = clean_sql_value(row[28])
                    if len(row) > 29 and row[29]:  # QA Completed Date
                        db_amendment.qa_completed_date = parse_date(clean_sql_value(row[29]))
                    if len(row) > 30 and row[30]:  # QA Notes
                        db_amendment.qa_notes = clean_sql_value(row[30])
                    if len(row) > 31 and row[31]:  # QA Test Plan Link
                        db_amendment.qa_test_plan_link = clean_sql_value(row[31])

                    imported_count += 1

                    if imported_count % 10 == 0:
                        print(f"Imported {imported_count} amendments...")

                except Exception as e:
                    # Show all errors to diagnose issues
                    print(f"Error importing amendment: {e}")
                    print(f"Row data (first 5 fields): {row[:5]}")
                    continue

        db.commit()
        print(f"\nSuccessfully imported {imported_count} amendments!")
        print(f"Skipped {skipped_count} rows (too few columns)")

    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    return imported_count


def main():
    """Main migration function."""
    print("=" * 60)
    print("Amendment System Data Migration")
    print("=" * 60)
    print()

    # Initialize database
    print("Initializing database...")
    init_db()

    # Path to old SQL dump - check multiple possible locations
    possible_paths = [
        Path(__file__).parent.parent.parent / 'fis-amendments' / 'script.sql',
        Path('/Users/wingle/Repos/fis-amendments/script.sql'),
    ]

    old_sql_path = None
    for path in possible_paths:
        if path.exists():
            old_sql_path = path
            break

    if not old_sql_path:
        old_sql_path = possible_paths[0]  # Use first path for error message

    if not old_sql_path.exists():
        print(f"Error: SQL dump file not found at {old_sql_path}")
        print("\nPlease provide the path to the script.sql file:")
        custom_path = input("> ").strip()
        if custom_path:
            old_sql_path = Path(custom_path)

        if not old_sql_path.exists():
            print("Error: File not found. Exiting.")
            return 1

    # Run migration
    try:
        count = migrate_amendments(old_sql_path)
        print(f"\nMigration complete! Imported {count} amendments.")
        return 0
    except Exception as e:
        print(f"\nMigration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
