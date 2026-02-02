#!/usr/bin/env python3
"""
Script to create or update the default admin user.

Creates a default admin user with credentials:
- Username: admin
- Password: admin123

WARNING: Change the default password in production!
"""

import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.database import SessionLocal
from backend.app import models
from backend.app.auth import hash_password


def create_or_update_admin():
    """Create or update the default admin user."""
    db = SessionLocal()

    try:
        # Check if admin user already exists
        admin = db.query(models.Employee).filter(
            models.Employee.windows_login == 'admin'
        ).first()

        if not admin:
            # Create new admin user
            admin = models.Employee(
                employee_name='System Administrator',
                initials='SA',
                email='admin@example.com',
                windows_login='admin',
                role='Admin',
                password_hash=hash_password('admin123'),
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

            print("=" * 60)
            print("Admin User Created Successfully!")
            print("=" * 60)
            print()
            print(f"  Employee ID: {admin.employee_id}")
            print(f"  Name: {admin.employee_name}")
            print(f"  Username: admin")
            print(f"  Password: admin123")
            print(f"  Role: Admin")
            print()
            print("⚠️  WARNING: Change the default password in production!")
            print()
            print("You can now login at: http://localhost:3000/login")
            print()

        else:
            # Update existing admin user
            admin.role = 'Admin'
            admin.password_hash = hash_password('admin123')
            admin.is_active = True
            db.commit()

            print("=" * 60)
            print("Admin User Updated Successfully!")
            print("=" * 60)
            print()
            print(f"  Employee ID: {admin.employee_id}")
            print(f"  Name: {admin.employee_name}")
            print(f"  Username: admin")
            print(f"  Password: admin123 (reset)")
            print(f"  Role: Admin")
            print()
            print("⚠️  WARNING: Change the default password in production!")
            print()

        return 0

    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1

    finally:
        db.close()


def main():
    """Main function."""
    return create_or_update_admin()


if __name__ == '__main__':
    sys.exit(main())
