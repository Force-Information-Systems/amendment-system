#!/bin/bash
# Script to backup and re-import amendment data with corrected mapping

echo "=========================================="
echo "Amendment System Data Re-import"
echo "=========================================="
echo ""

# Backup existing database
echo "Creating backup of existing database..."
BACKUP_FILE="amendment_system_backup_$(date +%Y%m%d_%H%M%S).db"
cp backend/amendment_system.db "backend/$BACKUP_FILE"
echo "Backup created: backend/$BACKUP_FILE"
echo ""

# Delete existing database
echo "Removing old database..."
rm backend/amendment_system.db
echo "Old database removed"
echo ""

# Run migration
echo "Running migration with corrected column mapping..."
cd /Users/wingle/Repos/amendment-system
python3 scripts/migrate_old_data.py

echo ""
echo "=========================================="
echo "Re-import complete!"
echo "=========================================="
echo ""
echo "To verify the import:"
echo "  sqlite3 backend/amendment_system.db \"SELECT COUNT(*) FROM amendments WHERE application IS NOT NULL;\""
echo ""
echo "To restore backup if needed:"
echo "  cp backend/$BACKUP_FILE backend/amendment_system.db"
