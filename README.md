# 🏀 NBA Betting Decision Engine

Machine learning-powered NBA player performance predictor for betting on player props.

## 🎯 What It Does

Predicts player stats for their next game:
- Points, Rebounds, Assists, Steals, Blocks, 3-Pointers
- Based on rolling averages and recent form
- **37.5% accuracy within ±3 points** (3.1x better than baseline)
- **Automatically updates daily** with latest games

## 🚀 Quick Start

```bash
streamlit run app/app.py
```

Open: **http://localhost:8501**

## 🔄 Automated Daily Updates

**Set it and forget it!** Your predictions update automatically every morning.

### Setup (One Time - Takes 30 seconds):

```bash
crontab -e
```

Add this line:
```
0 6 * * * /Users/bharathpalanisamy/nba-decision-engine/scripts/run_daily_update.sh >> /Users/bharathpalanisamy/nba-decision-engine/logs/daily_update.log 2>&1
```

**That's it!** Every day at 6 AM:
- ✅ Pulls latest NBA games
- ✅ Updates predictions automatically
- ✅ Ready for your betting decisions

See [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) for more options.

## 💰 How to Make Money

1. Open app → Select player
2. See prediction for their next game
3. Compare to sportsbook line
4. **If prediction < line**: Bet UNDER
5. **If prediction > line**: Bet OVER

**Example:**
- Sportsbook: LeBron O/U 24.5 points
- Prediction: 21.3 points  
- **BET: UNDER** (3.2 point edge)

## 📊 What You Get

- **Latest Games**: December 23, 2025 (updates daily)
- **Current Season**: 2025-26 games only
- **Model Training**: Both seasons (better accuracy)
- **Players**: 521 active players

## 🎲 Betting Tips

✅ **Check trends**: +/- vs Last 5 games  
✅ **Volume betting**: More bets = better odds  
✅ **Line shopping**: Compare multiple sportsbooks  
✅ **Confidence**: Bigger difference = more confident bet

## 📈 Accuracy

- Points: 37.5% within ±3
- Rebounds: 75.7% within ±3  
- Assists: 87.2% within ±3
- All other stats: 90%+ accuracy

**Trained on 36,986 games with 86 features**

## Manual Update (Optional)

If you want to update before the automated morning run:

```bash
python etl/update_daily.py
```

## 🔧 Files

- `app/app.py` - Web interface
- `etl/update_daily.py` - Automated updates
- `AUTOMATION_SETUP.md` - Detailed automation guide
- `logs/` - Update logs

## ⚠️ Disclaimer

For informational purposes only. Gamble responsibly.

---

**Good luck! 💰🏀**
