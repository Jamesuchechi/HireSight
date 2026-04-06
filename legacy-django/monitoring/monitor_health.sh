#!/bin/bash
# Health monitoring script for HireSight
# This script checks the health endpoint and logs the results

set -e  # Exit on any error

# Configuration
HEALTH_URL="http://localhost:8000/accounts/health/"
LOG_FILE="/home/jamesuchechi/Projects/HireSight/logs/health_monitor.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$TIMESTAMP] Checking health endpoint..." >> "$LOG_FILE"

# Check if the server is running
if curl -s --head "$HEALTH_URL" > /dev/null 2>&1; then
    # Get health status
    RESPONSE=$(curl -s "$HEALTH_URL")
    STATUS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))")

    if [ "$STATUS" = "healthy" ]; then
        echo "[$TIMESTAMP] ✅ Health check passed - Status: $STATUS" >> "$LOG_FILE"

        # Log system metrics
        CPU=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('system', {}).get('cpu_percent', 'N/A'))")
        MEMORY=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('system', {}).get('memory_percent', 'N/A'))")
        DISK=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('system', {}).get('disk_percent', 'N/A'))")

        echo "[$TIMESTAMP] System Metrics - CPU: ${CPU}%, Memory: ${MEMORY}%, Disk: ${DISK}%" >> "$LOG_FILE"
    else
        echo "[$TIMESTAMP] ❌ Health check failed - Status: $STATUS" >> "$LOG_FILE"
        echo "[$TIMESTAMP] Response: $RESPONSE" >> "$LOG_FILE"

        # Send alert (you can integrate with your alerting system here)
        echo "[$TIMESTAMP] 🚨 ALERT: Health check failed!" >> "$LOG_FILE"
    fi
else
    echo "[$TIMESTAMP] ❌ Cannot connect to health endpoint - Server may be down" >> "$LOG_FILE"
    echo "[$TIMESTAMP] 🚨 ALERT: Server is not responding!" >> "$LOG_FILE"
fi

echo "[$TIMESTAMP] Health check completed" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"