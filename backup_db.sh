#!/bin/bash
# Database backup script for HireSight (SQLite version)
# This script creates backups of the SQLite database

set -e  # Exit on any error

# Configuration
BACKUP_DIR="/home/jamesuchechi/Projects/HireSight/backups"
DB_FILE="/home/jamesuchechi/Projects/HireSight/db.sqlite3"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database file exists
if [ ! -f "$DB_FILE" ]; then
    echo "❌ Database file not found: $DB_FILE"
    exit 1
fi

# Generate timestamp for backup file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/hiresight_backup_$TIMESTAMP.sqlite3"

echo "Starting SQLite database backup..."
echo "Source: $DB_FILE"
echo "Destination: $BACKUP_FILE"

# Create backup by copying the SQLite file
cp "$DB_FILE" "$BACKUP_FILE"

# Verify backup was created successfully
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    echo "✅ Database backup completed successfully!"
    echo "Backup saved to: $BACKUP_FILE"

    # Get backup file size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup size: $BACKUP_SIZE"

    # Clean up old backups (keep last 7 days)
    echo "Cleaning up old backups..."
    find "$BACKUP_DIR" -name "hiresight_backup_*.sqlite3" -mtime +7 -delete
    echo "✅ Old backups cleaned up"

else
    echo "❌ Database backup failed!"
    exit 1
fi

echo "Backup process completed."