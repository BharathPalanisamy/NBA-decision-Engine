import pandas as pd
import joblib
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error

def predict_with_improved_models():
    """Test improved models on recent unseen data."""
    
    # Load features
    df = pd.read_csv("data/processed/player_features.csv")
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    # Filter for meaningful games (≥15 minutes)
    df = df[df['minutes'] >= 15].copy()
    
    # Engineer features (same as training)
    df = df.sort_values(['player_id', 'game_date'])
    df['prev_game_date'] = df.groupby('player_id')['game_date'].shift(1)
    df['rest_days'] = (df['game_date'] - df['prev_game_date']).dt.days
    df['rest_days'] = df['rest_days'].fillna(3).clip(0, 7)
    df['is_b2b'] = (df['rest_days'] <= 1).astype(int)
    df['pts_trend'] = df['avg_points_3'] - df['avg_points_10']
    df['min_trend'] = df['avg_minutes_3'] - df['avg_minutes_10']
    df['shots_per_min_3'] = df['avg_shots_attempted_3'] / (df['avg_minutes_3'] + 1)
    df['shots_per_min_5'] = df['avg_shots_attempted_5'] / (df['avg_minutes_5'] + 1)
    df['recent_efficiency'] = df['avg_fg_pct_3'] * df['avg_shots_attempted_3']
    
    # Fill NaN
    for col in ['rest_days', 'is_b2b', 'pts_trend', 'min_trend', 'shots_per_min_3', 
                'shots_per_min_5', 'recent_efficiency']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    # Get most recent 1000 games for validation
    df_test = df.sort_values('game_date').tail(1000).copy()
    
    print(f"🔍 Testing improved models on {len(df_test):,} recent games (≥15 min)\n")
    
    # Test each model
    stats = ['points', 'rebounds', 'assists', 'steals', 'blocks', 'fg3m']
    
    print(f"{'Model':<12} | {'MAE':<6} | {'±1':<7} | {'±3':<7} | {'±5':<7} | {'Avg Actual'}")
    print("-" * 75)
    
    results = {}
    for stat in stats:
        try:
            # Load model and features
            model = joblib.load(f'models/{stat}_model_v2.pkl')
            feature_cols = joblib.load(f'models/{stat}_model_features.pkl')
            
            # Prepare data
            df_stat = df_test[feature_cols + [stat]].dropna()
            
            if len(df_stat) < 50:
                continue
            
            X = df_stat[feature_cols]
            y_actual = df_stat[stat]
            
            # Predict
            y_pred = model.predict(X)
            
            # Metrics
            mae = abs(y_pred - y_actual).mean()
            within_1 = (abs(y_pred - y_actual) <= 1).mean() * 100
            within_3 = (abs(y_pred - y_actual) <= 3).mean() * 100
            within_5 = (abs(y_pred - y_actual) <= 5).mean() * 100
            
            print(f"{stat:<12} | {mae:<6.2f} | {within_1:<6.1f}% | {within_3:<6.1f}% | {within_5:<6.1f}% | {y_actual.mean():.1f}")
            
            results[stat] = {
                'mae': mae,
                'within_3': within_3,
                'within_5': within_5,
                'samples': len(df_stat)
            }
            
        except Exception as e:
            print(f"{stat:<12} | Error: {str(e)[:40]}")
    
    # Highlight points improvement
    if 'points' in results:
        print("\n" + "="*75)
        print("🎯 FINAL POINTS MODEL PERFORMANCE:")
        print(f"   Within ±3 points: {results['points']['within_3']:.1f}% (was 12.2% baseline)")
        print(f"   Within ±5 points: {results['points']['within_5']:.1f}%")
        print(f"   Test samples: {results['points']['samples']:,}")
        
        improvement = results['points']['within_3'] - 12.2
        print(f"\n   ✅ Improvement: +{improvement:.1f} percentage points")
        print(f"   ✅ Total gain: {results['points']['within_3']/12.2:.1f}x better than baseline")
        print("="*75)

if __name__ == "__main__":
    predict_with_improved_models()
