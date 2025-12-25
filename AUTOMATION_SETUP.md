# Automation Setup Guide

## Automated Daily Updates

Your NBA betting engine will automatically update every day with the latest games and predictions.

### What Gets Updated Automatically:
1. ✅ Latest games from current 2025-26 season
2. ✅ Player statistics and rolling averages
3. ✅ Feature calculations for predictions
4. ✅ Model predictions based on new data

### Setup Automation (Choose One Method):

---

## Method 1: macOS Cron Job (Recommended for Daily Use)

**Run updates every day at 6 AM:**

1. Open terminal and type:
```bash
crontab -e
```

2. Add this line (press `i` to enter insert mode in vi):
```bash
0 6 * * * /Users/bharathpalanisamy/nba-decision-engine/scripts/run_daily_update.sh >> /Users/bharathpalanisamy/nba-decision-engine/logs/daily_update.log 2>&1
```

3. Save and exit (press `ESC`, then type `:wq` and press `ENTER`)

4. Verify it's scheduled:
```bash
crontab -l
```

**This will automatically run every morning at 6 AM before games start!**

---

## Method 2: Manual Update Before Betting

If you prefer to manually update before checking predictions:

```bash
cd /Users/bharathpalanisamy/nba-decision-engine
python etl/update_daily.py
```

Then refresh your Streamlit app to see updated predictions.

---

## Method 3: Launch Agent (macOS - Always Running)

For a more robust solution that runs even after restarts:

1. Create the plist file:
```bash
nano ~/Library/LaunchAgents/com.nba.betting.update.plist
```

2. Add this content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nba.betting.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/bharathpalanisamy/nba-decision-engine/scripts/run_daily_update.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/bharathpalanisamy/nba-decision-engine/logs/daily_update.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/bharathpalanisamy/nba-decision-engine/logs/daily_update_error.log</string>
</dict>
</plist>
```

3. Load the agent:
```bash
launchctl load ~/Library/LaunchAgents/com.nba.betting.update.plist
```

4. Verify it's running:
```bash
launchctl list | grep nba
```

---

## Keep Streamlit Running 24/7

To keep your web app always accessible:

1. Install `screen` or `tmux`:
```bash
brew install tmux
```

2. Start a persistent session:
```bash
tmux new -s nba-app
cd /Users/bharathpalanisamy/nba-decision-engine
streamlit run app/app.py
```

3. Detach from session (press `Ctrl+B` then `D`)

4. Reattach later:
```bash
tmux attach -t nba-app
```

The Streamlit app will auto-reload when new data is available!

---

## Logs

Check update logs:
```bash
tail -f /Users/bharathpalanisamy/nba-decision-engine/logs/daily_update.log
```

---

## How It Works:

1. **Every day at 6 AM** (or when you run manually):
   - Script pulls latest games from NBA API
   - Updates your CSV with new games
   - Reloads data to PostgreSQL
   - Rebuilds features with rolling averages
   - Predictions automatically update

2. **Your Streamlit app**:
   - Automatically reloads when it detects new data
   - Shows updated predictions based on latest games
   - Ready for your daily betting decisions

---

## Test Your Automation

Run it manually once to verify:
```bash
cd /Users/bharathpalanisamy/nba-decision-engine
python etl/update_daily.py
```

Should see:
- ✅ Games pulled
- ✅ Database updated  
- ✅ Features rebuilt
- ✅ Ready for predictions

---

## Troubleshooting

If automation fails:
1. Check logs: `cat logs/daily_update.log`
2. Verify cron is running: `crontab -l`
3. Test script manually: `./scripts/run_daily_update.sh`
4. Ensure PostgreSQL container is running: `docker ps`

---

## Summary

**Once set up, your betting engine will:**
- 🔄 Update automatically every morning
- 📊 Always have latest player stats
- 🎯 Fresh predictions for today's games
- 💰 Ready for betting decisions

**You just need to:**
1. Open http://localhost:8501
2. Select player
3. See today's prediction
4. Make your bets!
