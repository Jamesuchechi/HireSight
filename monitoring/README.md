# HireSight Monitoring & Backup

This directory contains scripts for monitoring and backing up the HireSight application.

## Health Monitoring

The `monitor_health.sh` script checks the application's health endpoint and logs the results.

### Usage

```bash
# Run health check manually
./monitor_health.sh

# Set up cron job for regular monitoring (every 5 minutes)
crontab -e
# Add this line:
*/5 * * * * cd /home/jamesuchechi/Projects/HireSight && ./monitor_health.sh
```

### What it checks

- Database connectivity
- Cache functionality
- System resources (CPU, memory, disk usage)
- Overall application health

### Log files

- `/home/jamesuchechi/Projects/HireSight/logs/health_monitor.log`

## Database Backup

The `backup_db.sh` script creates backups of the SQLite database by copying the database file.

### Usage

```bash
# Run backup manually
./backup_db.sh

# Set up cron job for daily backups (at 2 AM)
crontab -e
# Add this line:
0 2 * * * cd /home/jamesuchechi/Projects/HireSight && ./backup_db.sh
```

### Configuration

The script is configured for SQLite and will:
- Copy the `db.sqlite3` file to the backups directory
- Add timestamp to backup filename
- Keep backups for 7 days automatically
- Verify backup file was created successfully

### Backup files

- Location: `/home/jamesuchechi/Projects/HireSight/backups/`
- Format: `hiresight_backup_YYYYMMDD_HHMMSS.sqlite3`
- Method: Simple file copy (SQLite databases are single files)

## Health Check Endpoint

The application includes a health check endpoint at `/accounts/health/` that returns JSON with system status.

### Response format

```json
{
  "status": "healthy",
  "timestamp": "2024-01-10T12:00:00.000000",
  "checks": {
    "database": "healthy",
    "cache": "healthy"
  },
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_percent": 23.1
  }
}
```

### Status codes

- `200`: All checks passed
- `503`: One or more checks failed

## Security Logs

Security events are logged to:
- `/home/jamesuchechi/Projects/HireSight/logs/security.log`
- `/home/jamesuchechi/Projects/HireSight/logs/django.log`

Monitor these files for security incidents, failed login attempts, and system errors.