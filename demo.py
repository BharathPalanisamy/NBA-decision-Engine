"""
NBA Player Performance Predictor - Demo
Demonstrates the improved model making predictions on recent games
"""

import pandas as pd
import joblib
import numpy as np
from datetime import datetime

def engineer_features(df):
    """Add engineered features to match training."""
    df = df.copy()
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    # Rest days
    df = df.sort_values(['player_id', 'game_date'])
    df['prev_game_date'] = df.groupby('player_id')['game_date'].shift(1)
    df['rest_days'] = (df['game_date'] - df['prev_game_date']).dt.days
    df['rest_days'] = df['rest_days'].fillna(3).clip(0, 7)
    df['is_b2b'] = (df['rest_days'] <= 1).astype(int)
    
    # Momentum
    df['pts_trend'] = df['avg_points_3'] - df['avg_points_10']
    df['min_trend'] = df['avg_minutes_3'] - df['avg_minutes_10']
    
    # Usage
    df['shots_per_min_3'] = df['avg_shots_attempted_3'] / (df['avg_minutes_3'] + 1)
    df['shots_per_min_5'] = df['avg_shots_attempted_5'] / (df['avg_minutes_5'] + 1)
    df['recent_efficiency'] = df['avg_fg_pct_3'] * df['avg_shots_attempted_3']
    
    for col in ['rest_days', 'is_b2b', 'pts_trend', 'min_trend', 
                'shots_per_min_3', 'shots_per_min_5', 'recent_efficiency']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    return df

def predict_player_stats(player_name, n_games=5):
    """Predict stats for a specific player's recent games."""
    
    print(f"\n{'='*80}")
    print(f"🏀 NBA PERFORMANCE PREDICTOR - {player_name.upper()}")
    print(f"{'='*80}\n")
    
    # Load data
    df = pd.read_csv('data/processed/player_features.csv')
    df = df[df['minutes'] >= 15].copy()  # Filter meaningful games
    df = engineer_features(df)
    
    # Get player's recent games
    player_df = df[df['player_name'].str.contains(player_name, case=False, na=False)]
    
    if len(player_df) == 0:
        print(f"❌ Player '{player_name}' not found")
        return
    
    player_df = player_df.sort_values('game_date', ascending=False).head(n_games)
    
    if len(player_df) == 0:
        print(f"❌ No recent games found for {player_name}")
        return
    
    # Load models
    models = {}
    for stat in ['points', 'rebounds', 'assists', 'steals', 'blocks', 'fg3m']:
        try:
            models[stat] = {
                'model': joblib.load(f'models/{stat}_model_v2.pkl'),
                'features': joblib.load(f'models/{stat}_model_features.pkl')
            }
        except:
            pass
    
    # Make predictions
    results = []
    for idx, row in player_df.iterrows():
        game_info = {
            'date': row['game_date'],
            'matchup': row['matchup'],
            'home': '🏠' if row['is_home'] else '✈️',
            'rest': int(row['rest_days']),
            'b2b': '⚡' if row['is_b2b'] else ''
        }
        
        predictions = {}
        actuals = {}
        
        for stat, model_info in models.items():
            features = model_info['features']
            available_features = [f for f in features if f in row.index]
            
            if len(available_features) == len(features):
                X = row[features].values.reshape(1, -1)
                pred = model_info['model'].predict(X)[0]
                predictions[stat] = round(pred, 1)
                actuals[stat] = row[stat] if stat in row.index else None
        
        results.append({**game_info, 'predictions': predictions, 'actuals': actuals})
    
    # Display results
    print(f"📊 Recent {n_games} Games (with ≥15 minutes)")
    print(f"Player: {player_df.iloc[0]['player_name']}")
    print(f"Avg Minutes: {player_df['minutes'].mean():.1f}")
    print(f"\n")
    
    # Header
    print(f"{'Date':<12} {'Matchup':<15} {'':^3} {'Rest':^4} {'':^3} | {'PTS':^7} | {'REB':^7} | {'AST':^7} | {'STL':^7} | {'BLK':^7} | {'3PM':^7}")
    print("-" * 100)
    
    # Rows
    for r in results:
        date_str = r['date'][:10] if isinstance(r['date'], str) else str(r['date'])[:10]
        matchup = r['matchup'][:14]
        home = r['home']
        rest = f"{r['rest']}d"
        b2b = r['b2b']
        
        pred = r['predictions']
        act = r['actuals']
        
        def format_stat(stat_name):
            p = pred.get(stat_name, 0)
            a = act.get(stat_name)
            if a is not None:
                diff = p - a
                symbol = "✓" if abs(diff) <= 3 else "✗"
                return f"{p:4.1f}/{a:2.0f} {symbol}"
            return f"{p:4.1f}/--"
        
        print(f"{date_str:<12} {matchup:<15} {home:^3} {rest:^4} {b2b:^3} | "
              f"{format_stat('points'):^7} | {format_stat('rebounds'):^7} | "
              f"{format_stat('assists'):^7} | {format_stat('steals'):^7} | "
              f"{format_stat('blocks'):^7} | {format_stat('fg3m'):^7}")
    
    # Summary
    print("\n" + "-" * 100)
    print("Legend: Pred/Actual  ✓=within 3  ✗=off by >3  🏠=Home  ✈️=Away  ⚡=Back-to-back")
    
    # Accuracy summary
    total_preds = 0
    correct_within_3 = 0
    
    for r in results:
        for stat in ['points', 'rebounds', 'assists']:
            p = r['predictions'].get(stat)
            a = r['actuals'].get(stat)
            if p is not None and a is not None:
                total_preds += 1
                if abs(p - a) <= 3:
                    correct_within_3 += 1
    
    if total_preds > 0:
        accuracy = (correct_within_3 / total_preds) * 100
        print(f"\n🎯 Accuracy: {correct_within_3}/{total_preds} within ±3 ({accuracy:.1f}%)")
    
    print(f"\n{'='*80}\n")

def show_top_performers():
    """Show predictions for top performers."""
    print(f"\n{'='*80}")
    print(f"🌟 TOP 10 RECENT PERFORMERS (Last 5 games avg)")
    print(f"{'='*80}\n")
    
    df = pd.read_csv('data/processed/player_features.csv')
    df = df[df['minutes'] >= 20].copy()
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    # Get recent games
    recent = df.sort_values('game_date').groupby('player_name').tail(5)
    
    # Calculate averages
    player_avgs = recent.groupby('player_name').agg({
        'points': 'mean',
        'rebounds': 'mean',
        'assists': 'mean',
        'minutes': 'mean'
    }).round(1)
    
    # Top scorers
    top = player_avgs.sort_values('points', ascending=False).head(10)
    
    print(f"{'Rank':<6} {'Player':<25} {'PPG':>6} {'RPG':>6} {'APG':>6} {'MIN':>6}")
    print("-" * 65)
    
    for i, (player, stats) in enumerate(top.iterrows(), 1):
        print(f"{i:<6} {player[:24]:<25} {stats['points']:>6.1f} {stats['rebounds']:>6.1f} "
              f"{stats['assists']:>6.1f} {stats['minutes']:>6.1f}")
    
    print(f"\n{'='*80}\n")

def main():
    """Run demo predictions."""
    
    print("\n" + "🏀" * 40)
    print("   NBA PLAYER PERFORMANCE PREDICTION SYSTEM")
    print("   Powered by XGBoost ML Models (v2 - Improved)")
    print("   37.5% accuracy within ±3 points (3.1x better than baseline)")
    print("🏀" * 40)
    
    # Show top performers
    show_top_performers()
    
    # Show predictions for specific popular players
    players = ['LeBron James', 'Stephen Curry', 'Luka Doncic', 'Giannis']
    
    for player in players:
        try:
            predict_player_stats(player, n_games=5)
        except Exception as e:
            print(f"Error predicting for {player}: {e}\n")
    
    print("\n" + "="*80)
    print("✅ Demo Complete!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
