#!/bin/bash
# Setup automatic nightly updates for NBA Betting Props Engine

PROJECT_DIR="/Users/bharathpalanisamy/nba-decision-engine"
LOG_DIR="$PROJECT_DIR/logs"

echo "🔧 Setting up automatic nightly updates..."
echo ""

# Create logs directory
mkdir -p "$LOG_DIR"

# Create the cron job entry
# Runs every night at 2:00 AM
CRON_JOB="0 2 * * * cd $PROJECT_DIR && ./refresh_data.sh >> $LOG_DIR/auto_update.log 2>&1"

# Check if cron job already exists
crontab -l 2>/dev/null | grep -q "refresh_data.sh"
if [ $? -eq 0 ]; then
    echo "⚠️  Cron job already exists. Removing old one..."
    crontab -l | grep -v "refresh_data.sh" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Automatic updates configured!"
echo ""
echo "📅 Schedule: Every night at 2:00 AM"
echo "📂 Logs saved to: $LOG_DIR/auto_update.log"
echo ""
echo "To view your cron jobs: crontab -l"
echo "To view logs: tail -f $LOG_DIR/auto_update.log"
echo "To remove auto-updates: crontab -l | grep -v 'refresh_data.sh' | crontab -"
echo ""
echo "🎲 Next update: Tonight at 2:00 AM"
