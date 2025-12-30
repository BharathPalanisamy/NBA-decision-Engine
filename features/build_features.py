import pandas as pd
from sqlalchemy import create_engine
import numpy as np

DB_URL = "postgresql+psycopg2://postgres:password@localhost:5433/nba"

def create_rolling_features(df, stat_cols, windows=[3, 5, 10]):
    """Create rolling average features for multiple stats and windows"""
    features = {}
    
    for stat in stat_cols:
        for window in windows:
            col_name = f"avg_{stat}_{window}"
            features[col_name] = (
                df.groupby("player_id")[stat]
                  .shift(1)
                  .rolling(window)
                  .mean()
            )
    
    return pd.DataFrame(features)

def extract_opponent_and_location(matchup):
    """Extract opponent team and home/away from matchup string
    Examples: 'LAL vs. BOS' -> opponent='BOS', is_home=1
              'LAL @ BOS' -> opponent='BOS', is_home=0
    """
    if pd.isna(matchup):
        return None, None
    
    if ' vs. ' in matchup:
        opponent = matchup.split(' vs. ')[1]
        is_home = 1
    elif ' @ ' in matchup:
        opponent = matchup.split(' @ ')[1]
        is_home = 0
    else:
        opponent = None
        is_home = None
    
    return opponent, is_home

def main():
    engine = create_engine(DB_URL)

    # 1) Read raw data with ALL stats
    df = pd.read_sql("""
        SELECT player_id, player_name, game_date, matchup, season,
               minutes, points, rebounds, assists, steals, blocks, turnovers,
               fg3m, fg3a, fgm, fga, ftm, fta, plus_minus, personal_fouls
        FROM player_game_logs
        WHERE minutes IS NOT NULL
        ORDER BY player_id, game_date
    """, engine)
    
    # Load team defensive stats
    try:
        team_def = pd.read_sql("SELECT * FROM team_defense", engine)
        has_defense = True
    except:
        print("⚠️  No team defense data found, skipping opponent defense features")
        has_defense = False

    df["game_date"] = pd.to_datetime(df["game_date"])
    
    # 2) Extract opponent and home/away
    opponent_data = df['matchup'].apply(extract_opponent_and_location).tolist()
    df['opponent'] = [x[0] for x in opponent_data]
    df['is_home'] = [x[1] for x in opponent_data]
    
    # 2b) Add opponent defensive stats
    if has_defense:
        df = df.merge(
            team_def[['team_abbrev', 'season', 'pts_allowed']],
            left_on=['opponent', 'season'],
            right_on=['team_abbrev', 'season'],
            how='left'
        )
        df.drop('team_abbrev', axis=1, inplace=True)
    else:
        df['pts_allowed'] = None

    # 3) Calculate shooting percentages
    df["fg_pct"] = np.where(df["fga"] > 0, df["fgm"] / df["fga"], 0)
    df["fg3_pct"] = np.where(df["fg3a"] > 0, df["fg3m"] / df["fg3a"], 0)
    df["ft_pct"] = np.where(df["fta"] > 0, df["ftm"] / df["fta"], 0)
    
    # 4) Usage indicators
    df["shots_attempted"] = df["fga"] + (0.44 * df["fta"])
    df["usage_proxy"] = df["fga"] + df["fta"] + df["turnovers"]

    # 5) Create rolling features for all key stats
    stat_cols = [
        "minutes", "points", "rebounds", "assists", "steals", "blocks", "turnovers",
        "fg3m", "fgm", "fga", "ftm", "fta", "fg_pct", "fg3_pct", "ft_pct",
        "plus_minus", "shots_attempted", "usage_proxy"
    ]
    
    rolling_features = create_rolling_features(df, stat_cols, windows=[3, 5, 10])
    df = pd.concat([df, rolling_features], axis=1)

    # 6) Rest days + back-to-back
    df["prev_game_date"] = df.groupby("player_id")["game_date"].shift(1)
    df["rest_days"] = (df["game_date"] - df["prev_game_date"]).dt.days
    df["b2b"] = (df["rest_days"] == 1).astype(int)
    
    # 7) Recent form (last 3 games vs previous 7 games)
    df["pts_trend"] = df["avg_points_3"] - df["avg_points_10"]
    df["min_trend"] = df["avg_minutes_3"] - df["avg_minutes_10"]

    # 8) Drop rows without enough history (need 10 games)
    feature_df = df.dropna(subset=["avg_minutes_10", "rest_days"])

    # 9) Save features
    feature_df.to_csv("data/processed/player_features.csv", index=False)

    print(f"✅ Feature table created with {len(feature_df):,} rows")
    print(f"📊 Features per row: {len(feature_df.columns)}")
    print(f"🏀 Unique players: {feature_df['player_id'].nunique()}")

if __name__ == "__main__":
    main()
