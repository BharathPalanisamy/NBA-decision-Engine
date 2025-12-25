# NBA Decision Engine 🏀

A machine learning system I built to predict NBA player performance and make smarter betting decisions on player props. After months of development and testing, I've achieved **37.5% accuracy within ±3 points** for player scoring predictions - which is about 3x better than baseline guessing.

## Why I Built This

I've always been into NBA betting, but I was tired of making decisions based on gut feelings or outdated stats. I wanted something data-driven that could give me an actual edge. So I built this system that:

- Pulls the latest NBA game data automatically
- Calculates rolling averages and momentum trends
- Predicts player stats for upcoming games
- Updates itself daily without me having to do anything

The best part? It's working. The predictions have been consistently better than the betting lines, and I've been using it for my own bets this season.

## What It Does

This system predicts six key stats for any NBA player's next game:
- **Points** (the main one for betting)
- **Rebounds**
- **Assists**
- **Steals**
- **Blocks**
- **3-Pointers Made**

The predictions are based on:
- Recent performance (last 3, 5, and 10 games)
- Rest days and back-to-back games
- Home vs away splits
- Shooting efficiency trends
- Overall momentum

## The Results

After training on **36,986 games** across two seasons, here's what I'm getting:

| Stat | Accuracy (±3) | Accuracy (±5) |
|------|---------------|---------------|
| Points | 37.5% | 57.1% |
| Rebounds | 75.7% | 88.3% |
| Assists | 87.2% | 94.2% |
| Steals | 98.6% | 99.4% |
| Blocks | 99.1% | 99.6% |
| 3-Pointers | 93.3% | 97.8% |

The ±3 range is what matters for betting since most lines fall within that spread.

## Quick Start

### Prerequisites

You'll need:
- Python 3.8+
- PostgreSQL (I use Docker for this)
- About 5GB of disk space for the data

### Installation

1. **Clone the repo**
```bash
git clone https://github.com/BharathPalanisamy/NBA-decision-Engine.git
cd NBA-decision-Engine
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL**
```bash
docker run --name nba-postgres -e POSTGRES_PASSWORD=password -p 5433:5432 -d postgres
docker exec -i nba-postgres psql -U postgres < db/schema.sql
```

4. **Pull initial data** (takes about 10 minutes)
```bash
python etl/pull_gamelogs.py
python etl/load_to_postgres.py
python features/build_features.py
```

5. **Launch the app**
```bash
streamlit run app/app.py
```

Open http://localhost:8501 and you're good to go!

## How I Use It for Betting

My typical workflow:

1. **Morning routine** - Check which games are happening today
2. **Open the app** - Look up players I'm interested in betting on
3. **Compare predictions** - See how my model's prediction compares to the sportsbook line
4. **Make decisions**:
   - If my prediction is **2+ points lower** than the O/U → Bet UNDER
   - If my prediction is **2+ points higher** than the O/U → Bet OVER
   - If they're within 1-2 points → Skip or bet smaller

5. **Check trends** - I look at the recent performance chart and the +/- vs last 5 games to see if the player is hot or cold

### Example

Let's say LeBron's O/U is 25.5 points tonight:
- My app predicts: **22.3 points**
- Difference: **-3.2 points**
- Last 5 average: 23.1 (-0.8 trending down)
- **Decision**: Bet UNDER with confidence

## The Tech Stack

I built this with:

**Data & ML**
- `nba_api` - Official NBA stats API
- `XGBoost` - The ML model (tried others, this performed best)
- `scikit-learn` - Feature engineering and validation
- `pandas` - Data manipulation

**Database**
- `PostgreSQL` - Stores all the game logs
- `SQLAlchemy` - ORM for database operations

**Frontend**
- `Streamlit` - Web interface (super easy to build with)
- `Plotly` - Interactive charts

**Automation**
- Cron jobs - Daily updates run automatically at 6 AM

## Automated Updates

This was important to me - I didn't want to manually update data every day. So I built an automated system that:

1. Pulls latest NBA games every morning at 6 AM
2. Updates the database with new stats
3. Recalculates rolling averages and features
4. Refreshes predictions automatically

### Set it up once:

```bash
crontab -e
```

Add this line:
```
0 6 * * * /path/to/NBA-decision-Engine/scripts/run_daily_update.sh >> /path/to/NBA-decision-Engine/logs/daily_update.log 2>&1
```

That's it. Now every morning you wake up to fresh predictions.

## Project Structure

```
NBA-decision-Engine/
├── app/
│   └── app.py                     # Streamlit web interface
├── data/
│   ├── raw/                       # Raw game logs (CSV)
│   └── processed/                 # Engineered features
├── etl/
│   ├── pull_gamelogs.py          # Fetch data from NBA API
│   ├── load_to_postgres.py       # Load to database
│   └── update_daily.py           # Daily automation script
├── features/
│   └── build_features.py         # Feature engineering
├── models/
│   ├── train_improved.py         # Model training
│   ├── validate_improved.py      # Validation
│   └── *_model_v2.pkl            # Trained XGBoost models
├── scripts/
│   └── run_daily_update.sh       # Automation wrapper
└── docs/
    ├── README.md                 # This file
    ├── AUTOMATION_SETUP.md       # Detailed automation guide
    └── MODEL_PERFORMANCE.md      # Model details and metrics
```

## Things I Learned

Building this taught me a lot:

1. **More data isn't always better** - I started with 5 seasons but found that 2 recent seasons actually performed better. The game changes too much over time.

2. **Feature engineering matters more than the model** - I spent way more time on calculating the right rolling averages and trends than tuning XGBoost parameters.

3. **Garbage time is real** - Filtering out games where players played <15 minutes improved accuracy by 12%. Those end-of-blowout minutes mess up the stats.

4. **Rest days are crucial** - Players on back-to-backs score about 2.4 points less on average. The model learned this pattern really well.

5. **Betting is about edge, not perfection** - Even 37.5% accuracy gives you a real edge if you're disciplined about when to bet.

## Current Limitations

Being honest about what this doesn't do (yet):

- **No opponent defense** - Right now it's based purely on the player's recent form, not who they're playing against
- **No injury data** - I manually check injury reports before betting
- **No lineup changes** - Doesn't account for teammates being out
- **No live updates** - Predictions are generated once daily, not during games
- **No bankroll management** - That's on you to manage

Some of these I plan to add in future versions.

## Betting Tips (From My Experience)

Here's what's been working for me:

✅ **Use the trends** - The +/- vs last 5 games indicator is gold. If a guy is trending up and the prediction is still under the line, that's a strong under bet.

✅ **Volume is your friend** - Don't try to hit one huge parlay. Make consistent, data-driven bets and let the edge play out over time.

✅ **Shop lines** - Different sportsbooks have different lines. A 0.5 point difference can matter.

✅ **Trust the data, but use your brain** - If Giannis is listed as questionable, don't blindly bet his over even if the model says so.

✅ **Track your bets** - I keep a spreadsheet of my predictions vs actual results vs betting outcomes. It keeps me honest.

❌ **Don't chase losses** - Stick to your betting unit. A bad day doesn't mean the model is broken.

❌ **Don't force it** - If there's no edge, don't bet. It's okay to skip games.

## Future Improvements

Things I want to add:

- [ ] Opponent defensive ratings
- [ ] Team pace and offensive efficiency
- [ ] Player vs team historical matchups
- [ ] Injury impact predictions
- [ ] Real-time line value alerts
- [ ] Confidence scores for each prediction
- [ ] Mobile-friendly interface
- [ ] Integration with sportsbook APIs

## Contributing

This is a personal project, but if you have ideas or improvements, feel free to open an issue or PR. I'm especially interested in:
- Better feature engineering approaches
- Alternative ML models worth testing
- Ways to incorporate more contextual data

## Disclaimer

**Important**: This tool is for educational and informational purposes. Sports betting involves risk, and you can lose money. Only bet what you can afford to lose. Past performance doesn't guarantee future results.

I'm sharing this because I think it's interesting technically and it's been useful for me personally. But you're responsible for your own betting decisions. Gamble responsibly.

## License

MIT License - feel free to use this for your own projects.

## Contact

Questions? Found a bug? Want to discuss betting strategies?

Feel free to open an issue or reach out. I'm always interested in talking NBA analytics and betting.

---

**Good luck with your bets!** 🍀

*Built with ☕ and 🏀 by Bharath*

*Last updated: December 2025*
