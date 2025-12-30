# NBA Decision Engine

ML-based NBA player performance predictor for betting analysis.

## Overview

Built this to stop making random bets and actually use data. Scrapes NBA stats, trains XGBoost models, and predicts player props. Currently hitting 37.5% accuracy (±3 points) on scoring - not perfect but better than guessing.

Training data: 36k+ games from past 2 seasons. Updates automatically every morning.

## What It Predicts

- Points
- Rebounds  
- Assists
- Steals
- Blocks
- 3-Pointers

## Accuracy

| Stat | ±3 | ±5 |
|------|----|----|
| Points | 37.5% | 57.1% |
| Rebounds | 75.7% | 88.3% |
| Assists | 87.2% | 94.2% |
| Steals | 98.6% | 99.4% |
| Blocks | 99.1% | 99.6% |
| 3PM | 93.3% | 97.8% |

Points are hardest because there's more variance. Defensive stats are way easier to predict.

## Setup

**Requirements:**
- Python 3.8+
- PostgreSQL
- ~5GB disk space

**Install:**

```bash
git clone https://github.com/BharathPalanisamy/NBA-decision-Engine.git
cd NBA-decision-Engine
pip install -r requirements.txt
```

**Database:**
```bash
# using docker
docker run --name nba-postgres -e POSTGRES_PASSWORD=password -p 5433:5432 -d postgres
docker exec -i nba-postgres psql -U postgres < db/schema.sql
```

**Initial data pull:**
```bash
python etl/pull_gamelogs.py
python etl/load_to_postgres.py
python features/build_features.py
```

**Run it:**
```bash
streamlit run app/app.py
```

Go to http://localhost:8501

## How I Use It

1. Check tonight's games
2. Look up players I want to bet on
3. Compare my prediction vs sportsbook line
4. If difference is 2+ points, I bet it
5. Check the trend chart to see if player is hot/cold

Example: LeBron O/U is 25.5, my model says 22.3 → bet under.

## Tech

- nba_api - data source
- XGBoost - ML models
- PostgreSQL - storage  
- Streamlit - UI
- cron - daily automation

## Auto Updates

Don't want to manually refresh data. Set up a cron job:

```bash
crontab -e
```

Add:
```
0 6 * * * /path/to/scripts/run_daily_update.sh >> /path/to/logs/daily_update.log 2>&1
```

Now it pulls fresh data every morning at 6am.

## Structure

```
├── app/app.py              # streamlit UI
├── etl/                    # data pipeline
│   ├── pull_gamelogs.py   # fetch from NBA API
│   ├── load_to_postgres.py
│   └── update_daily.py    # automation script
├── features/               # feature engineering
├── models/                 # trained XGBoost models
└── scripts/               # automation helpers
```

## What I Learned

**More data ≠ better.** Started with 5 seasons, but 2 recent seasons actually performed better. Game changes too fast.

**Feature engineering > model tuning.** Spent way more time on rolling averages than XGBoost params. Made the biggest difference.

**Filter garbage time.** Players with <15 min skew the stats bad. Removing them boosted accuracy 12%.

**Rest matters.** Back-to-back games = -2.4 pts on average. Model picked this up automatically.

## Limitations

No opponent defense factored in yet. No injury data. No lineup changes. Predictions update once daily, not live.

Also doesn't manage bankroll for you - that's on you.

## Betting Notes

What's worked so far:

- Trust the trend indicators (+/- vs last 5 games)
- Make consistent bets, don't chase parlays
- Shop different sportsbook lines
- Skip games with no edge
- Track everything in a spreadsheet

What doesn't work:

- Forcing bets when there's no value
- Chasing losses
- Ignoring injury reports

## TODO

- [ ] Add opponent defensive ratings
- [ ] Team pace factors
- [ ] Injury impact model
- [ ] Confidence scores
- [ ] Mobile version

## Disclaimer

Educational project. Don't bet money you can't lose. I'm not responsible for your losses.

---

MIT License

Built by Bharath | Dec 2025
