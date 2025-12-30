"""Calculate team defensive stats from actual game data"""
import pandas as pd
from sqlalchemy import create_engine

DB_URL = "postgresql+psycopg2://postgres:password@localhost:5433/nba"

def calculate_team_defense():
    """Calculate how many points each team allows per game from actual games"""
    engine = create_engine(DB_URL)
    
    # Get all games with opponent info
    df = pd.read_sql("""
        SELECT matchup, points, season, game_date
        FROM player_game_logs
        WHERE matchup IS NOT NULL
    """, engine)
    
    # Extract which team the player's team played against and their team
    def parse_matchup(matchup):
        if ' vs. ' in matchup:
            player_team = matchup.split(' vs. ')[0]
            opponent = matchup.split(' vs. ')[1]
        elif ' @ ' in matchup:
            player_team = matchup.split(' @ ')[0]
            opponent = matchup.split(' @ ')[1]
        else:
            return None, None
        return player_team, opponent
    
    df[['player_team', 'opponent']] = df['matchup'].apply(
        lambda x: pd.Series(parse_matchup(x))
    )
    
    # Group by opponent team and calculate points they allowed
    # Points scored against them = points our players scored
    defense_stats = df.groupby(['opponent', 'season']).agg({
        'points': 'mean',  # Average points allowed per game
        'game_date': 'count'  # Number of games
    }).reset_index()
    
    defense_stats.columns = ['team_abbrev', 'season', 'pts_allowed', 'games']
    
    # Round to 1 decimal
    defense_stats['pts_allowed'] = defense_stats['pts_allowed'].round(1)
    
    return defense_stats

def main():
    engine = create_engine(DB_URL)
    
    print("Calculating defensive stats from game data...")
    defense_df = calculate_team_defense()
    
    # Save to database
    defense_df.to_sql('team_defense', engine, if_exists='replace', index=False)
    
    print(f"\n✅ Calculated defense for {len(defense_df)} team-seasons")
    print(f"📊 Sample:")
    print(defense_df.head(10).to_string())
    
if __name__ == "__main__":
    main()
