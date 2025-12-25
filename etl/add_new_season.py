"""
Pull current 2025-26 season games (October - December 2025)
"""
import time
import pandas as pd
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
from tqdm import tqdm

# Pull 2025-26 season - THE CURRENT SEASON
all_players = players.get_active_players()
print(f"Pulling 2025-26 season for {len(all_players)} players...")

new_games = []

for player in tqdm(all_players):
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
    except Exception as e:
        continue

if new_games:
    new_df = pd.concat(new_games, ignore_index=True)
    new_df['game_date'] = pd.to_datetime(new_df['GAME_DATE'])
    
    # Load existing data
    existing_df = pd.read_csv('data/raw/player_gamelogs.csv', low_memory=False)
    existing_df['game_date'] = pd.to_datetime(existing_df['game_date'], errors='coerce')
    
    # Remove old 2025-26 data (empty/NaN rows)
    existing_df = existing_df[existing_df['season'].isin(['2023-24', '2024-25'])]
    
    # Combine
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Save
    combined_df.to_csv('data/raw/player_gamelogs.csv', index=False)
    
    print(f"\n✅ Added {len(new_df)} games from 2025-26 season")
    print(f"✅ Total games now: {len(combined_df)}")
    print(f"✅ Latest date: {combined_df['game_date'].max()}")
else:
    print("No games found")
