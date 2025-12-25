"""
Daily automated update script
Pulls latest games, rebuilds features, ready for predictions
"""
import time
import pandas as pd
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
from tqdm import tqdm
from sqlalchemy import create_engine
import subprocess

print("=" * 80)
print("🏀 NBA BETTING ENGINE - DAILY UPDATE")
print("=" * 80)

# Step 1: Pull latest games for current season
print("\n📥 STEP 1: Pulling latest 2025-26 season games...")
all_players = players.get_active_players()

new_games = []
for player in tqdm(all_players, desc="Fetching game logs"):
    try:
        time.sleep(0.7)
        gamelog = playergamelog.PlayerGameLog(
            player_id=player['id'],
            season='2025-26'
        )
        df = gamelog.get_data_frames()[0]
        if len(df) > 0:
            df['player_id'] = player['id']
            df['player_name'] = player['full_name']
            df['season'] = '2025-26'
            new_games.append(df)
    except:
        continue

if new_games:
    new_df = pd.concat(new_games, ignore_index=True)
    new_df['game_date'] = pd.to_datetime(new_df['GAME_DATE'])
    
    # Load existing data
    existing_df = pd.read_csv('data/raw/player_gamelogs.csv', low_memory=False)
    existing_df['game_date'] = pd.to_datetime(existing_df['game_date'], errors='coerce')
    
    # Remove old 2025-26 data
    existing_df = existing_df[existing_df['season'].isin(['2023-24', '2024-25'])]
    
    # Fix column mapping for new data
    new_df['points'] = new_df['PTS']
    new_df['rebounds'] = new_df['REB']
    new_df['assists'] = new_df['AST']
    new_df['steals'] = new_df['STL']
    new_df['blocks'] = new_df['BLK']
    new_df['turnovers'] = new_df['TOV']
    new_df['fg3m'] = new_df['FG3M']
    new_df['fg3a'] = new_df['FG3A']
    new_df['fgm'] = new_df['FGM']
    new_df['fga'] = new_df['FGA']
    new_df['ftm'] = new_df['FTM']
    new_df['fta'] = new_df['FTA']
    new_df['plus_minus'] = new_df['PLUS_MINUS']
    new_df['personal_fouls'] = new_df['PF']
    new_df['minutes'] = new_df['MIN']
    new_df['matchup'] = new_df['MATCHUP']
    
    # Combine
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df.to_csv('data/raw/player_gamelogs.csv', index=False)
    
    print(f"✅ Updated with {len(new_df)} games from 2025-26 season")
    print(f"✅ Latest game date: {new_df['game_date'].max()}")
    print(f"✅ Total games: {len(combined_df):,}")
else:
    print("⚠️  No new games found")

# Step 2: Load to database
print("\n💾 STEP 2: Loading to PostgreSQL...")
subprocess.run(["python", "etl/load_to_postgres.py"], check=True)

# Step 3: Rebuild features
print("\n🔧 STEP 3: Rebuilding features...")
subprocess.run(["python", "features/build_features.py"], check=True)

# Step 4: Verify
print("\n✅ STEP 4: Verification...")
df = pd.read_csv('data/processed/player_features.csv')
df['game_date'] = pd.to_datetime(df['game_date'])
latest_date = df['game_date'].max()
season_2526_games = len(df[df['season']=='2025-26'])

print(f"📊 Latest game date: {latest_date.strftime('%Y-%m-%d')}")
print(f"📊 2025-26 season games: {season_2526_games:,}")
print(f"📊 Total feature rows: {len(df):,}")

print("\n" + "=" * 80)
print("✅ DAILY UPDATE COMPLETE - Ready for predictions!")
print("=" * 80)
