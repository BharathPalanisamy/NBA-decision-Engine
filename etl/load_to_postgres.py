import pandas as pd
from sqlalchemy import create_engine, text

CSV_PATH = "data/raw/player_gamelogs.csv"

# Docker Postgres is mapped to localhost:5433
DB_URL = "postgresql+psycopg2://postgres:password@localhost:5433/nba"

def main():
    df = pd.read_csv(CSV_PATH, low_memory=False)
    
    # Normalize column names - use uppercase if lowercase is missing
    if 'points' not in df.columns and 'PTS' in df.columns:
        df['points'] = df['PTS']
    if 'rebounds' not in df.columns and 'REB' in df.columns:
        df['rebounds'] = df['REB']
    if 'assists' not in df.columns and 'AST' in df.columns:
        df['assists'] = df['AST']
    if 'game_date' not in df.columns and 'GAME_DATE' in df.columns:
        df['game_date'] = df['GAME_DATE']
    if 'matchup' not in df.columns and 'MATCHUP' in df.columns:
        df['matchup'] = df['MATCHUP']
    
    # Keep only the columns we need
    columns_to_keep = [
        'player_id', 'player_name', 'season', 'game_date', 'matchup',
        'minutes', 'points', 'rebounds', 'assists', 'steals', 'blocks',
        'turnovers', 'fg3m', 'fg3a', 'fgm', 'fga', 'ftm', 'fta',
        'plus_minus', 'personal_fouls'
    ]
    df = df[[col for col in columns_to_keep if col in df.columns]]

    # Basic cleaning / types
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date
    df["minutes"] = pd.to_numeric(df["minutes"], errors="coerce")
    df["points"] = pd.to_numeric(df["points"], errors="coerce")
    df["rebounds"] = pd.to_numeric(df["rebounds"], errors="coerce")
    df["assists"] = pd.to_numeric(df["assists"], errors="coerce")
    df["steals"] = pd.to_numeric(df["steals"], errors="coerce")
    df["blocks"] = pd.to_numeric(df["blocks"], errors="coerce")
    df["turnovers"] = pd.to_numeric(df["turnovers"], errors="coerce")
    df["fg3m"] = pd.to_numeric(df["fg3m"], errors="coerce")
    df["fg3a"] = pd.to_numeric(df["fg3a"], errors="coerce")
    df["fgm"] = pd.to_numeric(df["fgm"], errors="coerce")
    df["fga"] = pd.to_numeric(df["fga"], errors="coerce")
    df["ftm"] = pd.to_numeric(df["ftm"], errors="coerce")
    df["fta"] = pd.to_numeric(df["fta"], errors="coerce")
    df["plus_minus"] = pd.to_numeric(df["plus_minus"], errors="coerce")
    df["personal_fouls"] = pd.to_numeric(df["personal_fouls"], errors="coerce")

    print(f"Loaded {len(df):,} games from CSV")

    engine = create_engine(DB_URL)

    # Load into Postgres in smaller chunks
    df.to_sql("player_game_logs", engine, if_exists="replace", index=False, chunksize=500)

    print(f"✅ Loaded {len(df):,} rows into player_game_logs")

if __name__ == "__main__":
    main()
