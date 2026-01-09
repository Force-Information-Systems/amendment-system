#!/usr/bin/env python3
"""
Data Migration Script: Import amendments from old SQL Server database export to new SQLite system.

This script:
1. Reads the SQL Server export file (UTF-16 encoded)
2. Parses INSERT statements for the Amendment table
3. Maps old schema columns to new schema
4. Imports data into the new SQLite database
5. Initializes AmendmentReferences counters
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path

# Paths
OLD_SQL_FILE = Path("/Users/wingle/Repos/fis-amendments/script.sql")
NEW_DB_FILE = Path("/Users/wingle/Repos/amendment-system/backend/amendment_system.db")

# Column mapping: Old DB column name -> New DB column name
COLUMN_MAPPING = {
    # Core identification
    "Amendment Id": "amendment_id",
    "Amendment Type": "amendment_type",
    "Amendment Reference": "amendment_reference",

    # Basic info
    "Date Reported": "date_reported",
    "Description": "description",
    "Amendment Status": "amendment_status",  # Use text status, not ID
    "Force": "force",
    "Reported By": "reported_by",
    "Application": "application",  # Will become null, use AmendmentApplication instead
    "Version": None,  # Skip - old "Version" field (reported version)
    "Assigned To": "assigned_to",
    "Applied Version": None,  # Skip - will be in AmendmentApplication
    "Priority": "priority",
    "Notes": "notes",

    # Development
    "Database Changes": "database_changes",
    "DB Upgrade Changes": "db_upgrade_changes",
    "Development Status Id": None,  # Skip - use text status
    "Release Notes": "release_notes",

    # QA
    "QA Assigned Id": "qa_assigned_id",
    "QA Assigned Date": "qa_assigned_date",
    "QA Test Plan Check": "qa_test_plan_check",
    "QA Test Release Notes Check": "qa_test_release_notes_check",
    "QA Completed": "qa_completed",
    "QA Signature": "qa_signature",
    "QA Completed Date": "qa_completed_date",
    "QA Notes": "qa_notes",
    "QA Test Plan Link": "qa_test_plan_link",

    # Audit
    "Created By": "created_by",
    "Created On": "created_on",
    "Modified By": "modified_by",
    "Modified On": "modified_on",

    # Skip these
    "Amendment Status Id": None,  # Use text status instead
}

# Status mapping: Old status -> New status
STATUS_MAPPING = {
    "Applied To Master": "Completed",
    "Released to Customers": "Deployed",
    "Completed": "Completed",
    "In Progress": "In Progress",
    "Testing": "Testing",
    "Open": "Open",
}

# Type mapping: Old type -> New type
TYPE_MAPPING = {
    "Enhancement": "Enhancement",
    "Fault": "Fault",
    "Suggestion": "Suggestion",
    "Bug": "Bug",
    "Feature": "Feature",
}

def parse_sql_insert(line):
    """
    Parse a SQL INSERT statement and extract values.

    Example line:
    INSERT [dbo].[Amendment] (...columns...) VALUES (2570, N'Enhancement', N'1000E(a)', ...)
    """
    # Extract VALUES clause
    values_match = re.search(r'VALUES\s*\((.*?)\)\s*$', line, re.IGNORECASE)
    if not values_match:
        return None

    values_str = values_match.group(1)

    # Parse values - handle NULL, strings, numbers, dates, bits
    values = []
    current_value = ""
    in_string = False
    paren_depth = 0

    i = 0
    while i < len(values_str):
        char = values_str[i]

        if char == "'" and (i == 0 or values_str[i-1] != "'"):
            in_string = not in_string
            current_value += char
        elif char == '(' and not in_string:
            paren_depth += 1
            current_value += char
        elif char == ')' and not in_string:
            paren_depth -= 1
            current_value += char
        elif char == ',' and not in_string and paren_depth == 0:
            values.append(current_value.strip())
            current_value = ""
        else:
            current_value += char

        i += 1

    # Add last value
    if current_value.strip():
        values.append(current_value.strip())

    return values

def clean_value(value):
    """Clean and convert a SQL value to Python value."""
    if not value or value.upper() == 'NULL':
        return None

    # CAST datetime - check this FIRST before string parsing
    cast_match = re.match(r"CAST\(N?'(.+?)'\s+AS\s+(DateTime|Date)\)", value, re.IGNORECASE)
    if cast_match:
        date_str = cast_match.group(1)
        try:
            # Parse datetime - handle both date and datetime formats
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('T', ' '))
            else:
                # Just a date, parse and convert to datetime
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return parsed_date
        except Exception as e:
            print(f"Warning: Could not parse date '{date_str}': {e}")
            return None

    # Remove N'' prefix for unicode strings
    if value.startswith("N'") and value.endswith("'"):
        # Extract string content and handle escaped quotes
        content = value[2:-1]
        content = content.replace("''", "'")
        return content

    # Regular string
    if value.startswith("'") and value.endswith("'"):
        content = value[1:-1]
        content = content.replace("''", "'")
        return content

    # Boolean bit values
    if value in ('0', '1'):
        return bool(int(value))

    # Numeric
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        return value

def map_status(old_status):
    """Map old status to new status."""
    if not old_status:
        return "Open"
    return STATUS_MAPPING.get(old_status, "Open")

def map_type(old_type):
    """Map old type to new type."""
    if not old_type:
        return "Bug"
    return TYPE_MAPPING.get(old_type, "Bug")

def determine_development_status(amendment_status, notes):
    """Determine development status from amendment status and notes."""
    if amendment_status in ("Deployed", "Completed"):
        return "Ready for QA"
    elif amendment_status == "Testing":
        return "Ready for QA"
    elif amendment_status == "In Progress":
        return "In Development"
    else:
        return "Not Started"

def main():
    print("="*80)
    print("AMENDMENT DATA MIGRATION")
    print("="*80)
    print(f"Source: {OLD_SQL_FILE}")
    print(f"Target: {NEW_DB_FILE}")
    print()

    if not OLD_SQL_FILE.exists():
        print(f"ERROR: Source file not found: {OLD_SQL_FILE}")
        return

    if not NEW_DB_FILE.exists():
        print(f"ERROR: Target database not found: {NEW_DB_FILE}")
        print("Please ensure the backend database is initialized first.")
        return

    # Connect to SQLite database
    conn = sqlite3.connect(NEW_DB_FILE)
    cursor = conn.cursor()

    print("Reading and parsing SQL file...")

    # Read SQL file (UTF-16 encoded)
    try:
        with open(OLD_SQL_FILE, 'r', encoding='utf-16') as f:
            sql_content = f.read()
    except UnicodeDecodeError:
        # Try UTF-8 if UTF-16 fails
        with open(OLD_SQL_FILE, 'r', encoding='utf-8') as f:
            sql_content = f.read()

    # Find INSERT statements for Amendment table
    # Split by lines and find complete INSERT...VALUES statements
    # Each INSERT is on a single line in the SQL file
    insert_statements = []
    for line in sql_content.split('\n'):
        if re.match(r'INSERT\s+\[dbo\]\.\[Amendment\]', line, re.IGNORECASE):
            insert_statements.append(line.strip())
    print(f"Found {len(insert_statements)} amendment records to migrate")

    if len(insert_statements) == 0:
        print("No INSERT statements found. Exiting.")
        return

    # Get column names from first INSERT
    first_insert = insert_statements[0]
    columns_match = re.search(r'INSERT\s+\[dbo\]\.\[Amendment\]\s+\(([^\)]+)\)', first_insert, re.IGNORECASE)
    if not columns_match:
        print("ERROR: Could not parse column names from INSERT statement")
        return

    column_names_str = columns_match.group(1)
    old_columns = [col.strip().strip('[]') for col in column_names_str.split(',')]

    print(f"Found {len(old_columns)} columns in source data")
    print()

    # Track reference counters
    ref_counters = {
        'Bug': 0,
        'Fault': 0,
        'Enhancement': 0,
        'Feature': 0,
        'Suggestion': 0,
        'Maintenance': 0,
        'Documentation': 0,
    }

    # Process each INSERT statement
    migrated_count = 0
    skipped_count = 0

    for idx, insert_stmt in enumerate(insert_statements, 1):
        # Parse values
        values = parse_sql_insert(insert_stmt)
        if not values:
            if idx <= 5 or idx % 200 == 0:  # Show first few and periodic errors
                print(f"Skipping record {idx}: Could not parse VALUES clause")
            skipped_count += 1
            continue
        if len(values) != len(old_columns):
            if idx <= 5:
                print(f"Skipping record {idx}: Column count mismatch (got {len(values)}, expected {len(old_columns)})")
            skipped_count += 1
            continue

        # Create a dictionary of old_column: value
        old_data = {}
        for i, col_name in enumerate(old_columns):
            old_data[col_name] = clean_value(values[i])

        # Map to new schema
        new_data = {}
        for old_col, new_col in COLUMN_MAPPING.items():
            if new_col and old_col in old_data:
                new_data[new_col] = old_data[old_col]

        # Apply transformations
        if 'amendment_type' in new_data:
            new_data['amendment_type'] = map_type(new_data['amendment_type'])

        if 'amendment_status' in new_data:
            new_data['amendment_status'] = map_status(new_data['amendment_status'])

        # Add development_status based on amendment_status
        new_data['development_status'] = determine_development_status(
            new_data.get('amendment_status'),
            new_data.get('notes')
        )

        # Set application to NULL (will use AmendmentApplication table later)
        new_data['application'] = None

        # Fix modified_on - if NULL, use created_on
        if not new_data.get('modified_on') and new_data.get('created_on'):
            new_data['modified_on'] = new_data['created_on']
        elif not new_data.get('modified_on'):
            new_data['modified_on'] = datetime.now()

        # Fix required fields that might be NULL in old data
        if not new_data.get('description'):
            new_data['description'] = '(No description provided)'

        if not new_data.get('priority'):
            new_data['priority'] = 'Medium'

        if not new_data.get('created_on'):
            # Use date_reported or current date
            new_data['created_on'] = new_data.get('date_reported') or datetime.now()

        if not new_data.get('development_status'):
            new_data['development_status'] = 'Not Started'

        # Update reference counter
        if new_data.get('amendment_type'):
            amd_type = new_data['amendment_type']
            # Extract number from reference (e.g., 1000E(a) -> 1000)
            ref = new_data.get('amendment_reference', '')
            match = re.match(r'(\d+)', ref)
            if match:
                ref_num = int(match.group(1))
                if ref_num > ref_counters.get(amd_type, 0):
                    ref_counters[amd_type] = ref_num

        # Insert into database
        try:
            columns = ', '.join(new_data.keys())
            placeholders = ', '.join(['?' for _ in new_data])
            sql = f"INSERT INTO amendments ({columns}) VALUES ({placeholders})"

            cursor.execute(sql, list(new_data.values()))
            migrated_count += 1

            if idx % 100 == 0:
                print(f"Processed {idx}/{len(insert_statements)} records...")
                conn.commit()

        except Exception as e:
            print(f"Error inserting record {idx} (ID: {old_data.get('Amendment Id')}): {e}")
            skipped_count += 1
            continue

    # Commit remaining
    conn.commit()

    # Initialize AmendmentReferences table
    print()
    print("Initializing reference counters...")

    # Check if reference record exists
    cursor.execute("SELECT COUNT(*) FROM amendment_references")
    if cursor.fetchone()[0] == 0:
        # Insert initial counters
        cursor.execute("""
            INSERT INTO amendment_references (
                bug_reference,
                fault_reference,
                enhancement_reference,
                feature_reference,
                suggestion_reference,
                maintenance_reference,
                documentation_reference
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ref_counters.get('Bug', 0),
            ref_counters.get('Fault', 0),
            ref_counters.get('Enhancement', 0),
            ref_counters.get('Feature', 0),
            ref_counters.get('Suggestion', 0),
            ref_counters.get('Maintenance', 0),
            ref_counters.get('Documentation', 0),
        ))
        conn.commit()
        print("Reference counters initialized:")
        for amd_type, count in ref_counters.items():
            print(f"  {amd_type}: {count}")

    conn.close()

    print()
    print("="*80)
    print("MIGRATION COMPLETE")
    print("="*80)
    print(f"Successfully migrated: {migrated_count} amendments")
    print(f"Skipped: {skipped_count} amendments")
    print(f"Total processed: {len(insert_statements)}")
    print()
    print("Next steps:")
    print("1. Review migrated data in the application")
    print("2. Create AmendmentApplication records for app/version tracking")
    print("3. Verify reference number generation continues from migrated data")

if __name__ == "__main__":
    main()
