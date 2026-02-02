#!/usr/bin/env python3
"""
Initialize reference data tables with values from enums.

This script populates the force_references, priority_references, and status_references
tables with the current enum values.
"""

import sqlite3
from pathlib import Path

# Database path
DB_FILE = Path("/Users/wingle/Repos/amendment-system/backend/amendment_system.db")

# Reference data from enums
FORCES = [
    "Avon And Somerset",
    "Bedfordshire, Cambridgeshire & Hertfordshire",
    "British Transport",
    "Cheshire",
    "Cleveland",
    "Cumbria",
    "Derbyshire",
    "Devon And Cornwall",
    "Durham",
    "Essex",
    "Gloucestershire",
    "Greater Manchester",
    "Gwent",
    "Hampshire",
    "Kent",
    "Lancashire",
    "Leicestershire",
    "Lincolnshire",
    "Merseyside",
    "Metropolitan",
    "Norfolk & Suffolk",
    "North Wales",
    "North Yorkshire",
    "Northumbria",
    "Nottinghamshire",
    "Police Scotland",
    "South Yorkshire",
    "Staffordshire",
    "Surrey",
    "Sussex",
    "Warwickshire & West Mercia",
    "West Midlands",
    "West Yorkshire",
    "Wiltshire",
    "FIS",
    "Home Office",
    "IPCC",
    "MOD",
    "NCUG",
    "PIRC",
    "UA",
]

PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

AMENDMENT_STATUSES = [
    "Open",
    "In Progress",
    "Testing",
    "Completed",
    "Deployed",
]

DEVELOPMENT_STATUSES = [
    "Not Started",
    "In Development",
    "Code Review",
    "Ready for QA",
]


def main():
    print("=" * 80)
    print("INITIALIZING REFERENCE DATA TABLES")
    print("=" * 80)
    print(f"Database: {DB_FILE}")
    print()

    if not DB_FILE.exists():
        print(f"ERROR: Database file not found: {DB_FILE}")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='force_references'"
        )
        if not cursor.fetchone():
            print("ERROR: force_references table does not exist. Run the app first to create tables.")
            return

        # Clear existing data
        print("Clearing existing reference data...")
        cursor.execute("DELETE FROM force_references")
        cursor.execute("DELETE FROM priority_references")
        cursor.execute("DELETE FROM status_references")
        conn.commit()

        # Insert Forces
        print(f"\nInserting {len(FORCES)} forces...")
        from datetime import datetime
        now = datetime.now().isoformat()
        for idx, force_name in enumerate(FORCES, 1):
            cursor.execute(
                """
                INSERT INTO force_references (force_name, is_active, sort_order, created_on, modified_on)
                VALUES (?, ?, ?, ?, ?)
                """,
                (force_name, True, idx, now, now),
            )
        print(f"  ✓ Inserted {len(FORCES)} forces")

        # Insert Priorities
        print(f"\nInserting {len(PRIORITIES)} priorities...")
        for idx, priority_name in enumerate(PRIORITIES, 1):
            cursor.execute(
                """
                INSERT INTO priority_references (priority_name, is_active, sort_order, created_on, modified_on)
                VALUES (?, ?, ?, ?, ?)
                """,
                (priority_name, True, idx, now, now),
            )
        print(f"  ✓ Inserted {len(PRIORITIES)} priorities")

        # Insert Amendment Statuses
        print(f"\nInserting {len(AMENDMENT_STATUSES)} amendment statuses...")
        for idx, status_name in enumerate(AMENDMENT_STATUSES, 1):
            cursor.execute(
                """
                INSERT INTO status_references (status_name, status_type, is_active, sort_order, created_on, modified_on)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (status_name, "amendment", True, idx, now, now),
            )
        print(f"  ✓ Inserted {len(AMENDMENT_STATUSES)} amendment statuses")

        # Insert Development Statuses
        print(f"\nInserting {len(DEVELOPMENT_STATUSES)} development statuses...")
        for idx, status_name in enumerate(DEVELOPMENT_STATUSES, 1):
            cursor.execute(
                """
                INSERT INTO status_references (status_name, status_type, is_active, sort_order, created_on, modified_on)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (status_name, "development", True, idx, now, now),
            )
        print(f"  ✓ Inserted {len(DEVELOPMENT_STATUSES)} development statuses")

        conn.commit()

        print()
        print("=" * 80)
        print("REFERENCE DATA INITIALIZATION COMPLETE")
        print("=" * 80)
        print(f"Total forces: {len(FORCES)}")
        print(f"Total priorities: {len(PRIORITIES)}")
        print(f"Total amendment statuses: {len(AMENDMENT_STATUSES)}")
        print(f"Total development statuses: {len(DEVELOPMENT_STATUSES)}")
        print()

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
