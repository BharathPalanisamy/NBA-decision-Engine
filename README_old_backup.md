# 🎲 NBA Betting Props Prediction Engine

A machine learning system that predicts NBA player statistics for betting props.

---

## 🎯 What Does This Do?

**Simple Answer:** Predicts how many points, rebounds, assists, etc. each NBA player will score in their next game.

**Example:**
- Predicts: "Stephen Curry will score 37.5 points"
- Recent Average: 32.0 points
- **Edge: +5.5 points** → Consider betting OVER on Curry's points

---

## 📊 Stats We Predict

✅ **Points** - Most common betting prop  
✅ **Rebounds** - Total boards  
✅ **Assists** - Dimes  
✅ **PRA** - Points + Rebounds + Assists combined  
✅ **3-Pointers Made** - Threes  
✅ **Steals** - Defensive stat  
✅ **Blocks** - Shot blocking  

---

## 🚀 How to Use

### 1. **View Predictions (Daily)**
```bash
streamlit run app/fantasy_app.py
```
Opens web app at http://localhost:8502

### 2. **Refresh Data (Get Latest Games)**
```bash
./refresh_data.sh
```
This pulls new NBA games, retrains models, and generates fresh predictions.

### 3. **Auto-Updates**
Data refreshes automatically every night at 2:00 AM. No action needed.

---

## 📱 The Web App (4 Tabs)

### Tab 1: Today's Props
- Shows all players with predictions
- Filter by location (Home/Away)
- See which props differ most from recent average
- Over/Under recommendations

### Tab 2: Player Props
- Deep dive into any specific player
- See 15-game performance trends
- Recent game log with all stats
- Confidence indicators

### Tab 3: Hot Picks
- High-confidence betting opportunities
- Players where prediction differs significantly from average
- Sorted by confidence score
- Shows edge for each stat

### Tab 4: Model Performance
- Which stats are most accurate
- Use this to know which props to trust
- Blocks/Steals = 70-85% accurate ⭐⭐⭐⭐⭐
- Points/Rebounds = 12-32% accurate ⭐⭐⭐

---

## 🗂️ Project Structure (What Each File Does)

```
nba-decision-engine/
│
├── app/
│   └── fantasy_app.py          # Web interface (Streamlit dashboard)
│
├── data/
│   ├── raw/
│   │   └── player_gamelogs.csv # Raw NBA game data
│   └── processed/
│       ├── player_features.csv # 85 features per player
│       └── predictions.csv     # Final predictions (395 players)
│
├── db/
│   └── schema.sql              # PostgreSQL database structure
│
├── etl/
│   ├── pull_gamelogs.py        # Downloads NBA data from API
│   └── load_to_postgres.py    # Saves data to database
│
├── features/
│   └── build_features.py       # Creates 85 features (rolling averages, etc.)
│
├── models/
│   ├── train_all_models.py     # Trains 6 XGBoost models
│   ├── predict_betting_props.py # Generates predictions
│   ├── points_model.pkl        # Trained model files
│   ├── rebounds_model.pkl
│   ├── assists_model.pkl
│   ├── steals_model.pkl
│   ├── blocks_model.pkl
│   └── fg3m_model.pkl
│
├── logs/
│   └── auto_update.log         # Automatic update history
│
└── refresh_data.sh             # One-click data refresh
```

---

## 🔄 How It Works (Simple Flow)

```
1. NBA API → Download game logs (9,306 games)
                ↓
2. PostgreSQL → Store in database
                ↓
3. Feature Engineering → Create 85 features per player
   (rolling averages, opponent data, home/away, rest days)
                ↓
4. XGBoost Models → Train 6 separate models (one per stat)
                ↓
5. Predictions → Generate predictions for all 395 players
                ↓
6. Streamlit App → Display in web dashboard
```

---

## 🤖 The Machine Learning (Simplified)

### What Are "Features"?
Features = Data the model uses to make predictions

**Example for LeBron James:**
- Average points last 3 games: 24.3
- Average points last 5 games: 22.0
- Average points last 10 games: 18.6
- Playing at: Home (yes/no)
- Days of rest: 2
- Opponent: LAC
- Back-to-back game: No
- Recent trend: +5.7 points per game
- *...and 77 more features*

### How Models Work:
1. Train on **4,831 historical games**
2. Learn patterns (e.g., "LeBron scores more at home with 2+ days rest")
3. Use those patterns to predict next game
4. **Test accuracy**: Cross-validation on held-out data

### Model Accuracy:
- **Blocks**: 85.8% within ±1 (excellent!)
- **Steals**: 71.9% within ±1 (excellent!)
- **Assists**: 45.1% within ±1 (good)
- **Points**: 12.2% within ±1 (fair - harder to predict)

---

## 📅 Typical Daily Workflow

**Morning Before Games:**
```bash
# Check if data is fresh (should auto-update at 2 AM)
ls -la data/processed/predictions.csv

# If needed, manually refresh
./refresh_data.sh

# Launch app
streamlit run app/fantasy_app.py
```

**In the App:**
1. Go to "Hot Picks" tab
2. Look for high-confidence opportunities (green indicators)
3. Compare our prediction to your sportsbook's line
4. Place bets where you see value

**Example Decision:**
```
Our Prediction: Curry 37.5 points
Sportsbook Line: Curry O/U 32.5 points
Difference: +5 points
Confidence: 🟢 High (based on recent performance spike)
Action: Consider OVER bet
```

---

## 🛠️ Maintenance Commands

### View Recent Logs
```bash
tail -50 logs/auto_update.log
```

### Check Cron Job (Auto-Updates)
```bash
crontab -l
```

### Manual Data Refresh
```bash
./refresh_data.sh
```

### Retrain Models Only (if you have new data)
```bash
python models/train_all_models.py
python models/predict_betting_props.py
```

### Check Database
```bash
docker ps  # See if PostgreSQL is running
```

---

## ⚠️ Important Notes

### What This DOES:
✅ Predicts player stats with ML models  
✅ Shows edge vs. recent average  
✅ Updates automatically every night  
✅ Tracks model accuracy  

### What This DOESN'T Do:
❌ Pull actual sportsbook betting lines  
❌ Tell you exactly what to bet  
❌ Guarantee winning bets  
❌ Account for injuries (yet)  

### Always Remember:
- **Use model performance tab** to see which stats are reliable
- **Steals/Blocks** = Most accurate (trust these)
- **Points** = Less accurate (use with caution)
- **Compare to sportsbook lines manually** before betting
- This is a tool to inform decisions, not make them for you

---

## 🐛 Troubleshooting

### App won't load?
```bash
# Restart the app
pkill -f "streamlit run"
streamlit run app/fantasy_app.py
```

### No recent data?
```bash
# Manually refresh
./refresh_data.sh
```

### Database connection error?
```bash
# Check if PostgreSQL is running
docker ps

# Restart if needed
docker start nba_postgres
```

### Cron job not running?
```bash
# Check it exists
crontab -l

# Re-add if missing
./setup_auto_update.sh
```

---

## 📈 Understanding Model Performance

**MAE (Mean Absolute Error):**
- Average prediction error
- Lower = Better
- Blocks MAE = 0.58 (predicts within 0.58 blocks on average)

**Within ±1:**
- % of predictions within 1 unit of actual
- Higher = Better
- Blocks = 85.8% (very reliable)
- Points = 12.2% (less reliable)

**Use This Knowledge:**
- Trust blocks/steals predictions more
- Be cautious with points predictions
- Combine multiple factors for best bets

---

## 🎓 Key Concepts

**PRA:** Points + Rebounds + Assists (popular parlay prop)

**Edge:** How much our prediction differs from recent average  
- Example: Predicted 30 pts, Average 25 pts → +5 edge

**Rolling Average:** Average over last N games (we use 3, 5, and 10)

**Cross-Validation:** Testing model on data it hasn't seen (prevents overfitting)

**XGBoost:** Type of ML algorithm (Gradient Boosted Decision Trees)

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Launch app | `streamlit run app/fantasy_app.py` |
| Refresh data | `./refresh_data.sh` |
| View logs | `tail -50 logs/auto_update.log` |
| Check schedule | `crontab -l` |
| Stop app | `pkill -f "streamlit run"` |

**App URL:** http://localhost:8502  
**Update Time:** 2:00 AM daily (automatic)  
**Data Source:** NBA API (official stats)  
**Players:** 395 active players  
**Season:** 2025-26

---

🎲 **Remember:** This predicts stats, not betting outcomes. Always bet responsibly and within your means.
