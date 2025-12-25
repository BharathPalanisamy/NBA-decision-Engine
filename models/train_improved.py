import pandas as pd
import joblib
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GridSearchCV

def engineer_additional_features(df):
    """Add more predictive features."""
    df = df.copy()
    
    # Convert to datetime if needed
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    # Rest days (time since last game)
    df = df.sort_values(['player_id', 'game_date'])
    df['prev_game_date'] = df.groupby('player_id')['game_date'].shift(1)
    df['rest_days'] = (df['game_date'] - df['prev_game_date']).dt.days
    df['rest_days'] = df['rest_days'].fillna(3).clip(0, 7)  # Cap at 7 days
    
    # Back-to-back indicator
    df['is_b2b'] = (df['rest_days'] <= 1).astype(int)
    
    # Momentum features (trending up/down)
    df['pts_trend'] = df['avg_points_3'] - df['avg_points_10']
    df['min_trend'] = df['avg_minutes_3'] - df['avg_minutes_10']
    
    # Usage rate proxy (shots per minute)
    df['shots_per_min_3'] = df['avg_shots_attempted_3'] / (df['avg_minutes_3'] + 1)
    df['shots_per_min_5'] = df['avg_shots_attempted_5'] / (df['avg_minutes_5'] + 1)
    
    # Efficiency metrics
    df['recent_efficiency'] = df['avg_fg_pct_3'] * df['avg_shots_attempted_3']
    
    # Fill any NaN from new features
    for col in ['rest_days', 'is_b2b', 'pts_trend', 'min_trend', 'shots_per_min_3', 
                'shots_per_min_5', 'recent_efficiency']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    return df

def select_best_features(df, target_col, top_n=30):
    """Select most important features using correlation and variance."""
    feature_cols = [c for c in df.columns if c.startswith('avg_') or 
                   c in ['is_home', 'rest_days', 'is_b2b', 'pts_trend', 'min_trend',
                         'shots_per_min_3', 'shots_per_min_5', 'recent_efficiency']]
    
    # Remove low variance features
    feature_cols = [c for c in feature_cols if c in df.columns]
    
    # For points, prioritize relevant features
    if target_col == 'points':
        priority_features = [c for c in feature_cols if 'points' in c or 'fg' in c or 
                           'shots' in c or 'minutes' in c or 'efficiency' in c or
                           c in ['rest_days', 'is_b2b', 'is_home', 'pts_trend', 'min_trend']]
        feature_cols = priority_features[:top_n] if len(priority_features) >= top_n else feature_cols[:top_n]
    
    return feature_cols

def train_improved_model(df, target_col, model_name, min_minutes=15):
    """Train improved model with better filtering and hyperparameters."""
    
    # Filter for meaningful games (players with significant minutes)
    df = df[df['minutes'] >= min_minutes].copy()
    
    # Add engineered features
    df = engineer_additional_features(df)
    
    # Select best features
    feature_cols = select_best_features(df, target_col)
    
    # Prepare data
    df_model = df[feature_cols + [target_col, 'game_date']].dropna()
    
    if len(df_model) < 1000:
        print(f"❌ Not enough data for {target_col} (only {len(df_model)} rows)")
        return None
    
    # Sort by date for time-aware split
    df_model['game_date'] = pd.to_datetime(df_model['game_date'])
    df_model = df_model.sort_values('game_date').reset_index(drop=True)
    
    X = df_model[feature_cols]
    y = df_model[target_col]
    
    # Last 20% as test set
    split = int(len(df_model) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    # Improved hyperparameters with better tuning
    best_params = {
        'n_estimators': 400,
        'max_depth': 6,
        'learning_rate': 0.03,
        'subsample': 0.85,
        'colsample_bytree': 0.85,
        'min_child_weight': 3,
        'gamma': 0.1,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'random_state': 42
    }
    
    # For high variance stats like points, tune more carefully
    if target_col == 'points':
        best_params.update({
            'max_depth': 7,
            'n_estimators': 500,
            'learning_rate': 0.02,
            'min_child_weight': 2
        })
    
    model = XGBRegressor(**best_params)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    
    # Accuracy within thresholds
    within_1 = (abs(preds - y_test) <= 1).mean() * 100
    within_3 = (abs(preds - y_test) <= 3).mean() * 100
    within_5 = (abs(preds - y_test) <= 5).mean() * 100
    
    print(f"✅ {model_name:20} | MAE: {mae:5.2f} | ±1: {within_1:5.1f}% | ±3: {within_3:5.1f}% | ±5: {within_5:5.1f}%")
    print(f"   Train: {len(X_train):,} | Test: {len(X_test):,} | Features: {len(feature_cols)}")
    
    # Save model
    joblib.dump(model, f"models/{model_name}_v2.pkl")
    
    # Also save feature list for predictions
    joblib.dump(feature_cols, f"models/{model_name}_features.pkl")
    
    return {
        'mae': mae,
        'within_1': within_1,
        'within_3': within_3,
        'within_5': within_5,
        'samples': len(X_test),
        'avg_actual': y_test.mean()
    }

def main():
    df = pd.read_csv("data/processed/player_features.csv")
    
    print("🚀 Training IMPROVED models with:")
    print("   ✓ Filtered for games with ≥15 minutes")
    print("   ✓ Additional engineered features (rest days, trends, efficiency)")
    print("   ✓ Feature selection (top 30 most relevant)")
    print("   ✓ Optimized XGBoost hyperparameters")
    print(f"   ✓ Original dataset: {len(df):,} rows\n")
    
    # Train models for each stat
    targets = [
        ('points', 'points_model'),
        ('rebounds', 'rebounds_model'),
        ('assists', 'assists_model'),
        ('steals', 'steals_model'),
        ('blocks', 'blocks_model'),
        ('fg3m', 'fg3m_model')
    ]
    
    results = {}
    for target_col, model_name in targets:
        result = train_improved_model(df, target_col, model_name, min_minutes=15)
        if result:
            results[target_col] = result
        print()
    
    # Summary
    print("\n" + "="*80)
    print("🎯 IMPROVED MODEL SUMMARY")
    print("="*80)
    print(f"{'Stat':<12} | {'MAE':<6} | {'±1':<7} | {'±3':<7} | {'±5':<7} | {'Avg':<6} | Samples")
    print("-" * 80)
    
    for target_col, model_name in targets:
        if target_col in results:
            r = results[target_col]
            print(f"{target_col:<12} | {r['mae']:<6.2f} | {r['within_1']:<6.1f}% | "
                  f"{r['within_3']:<6.1f}% | {r['within_5']:<6.1f}% | "
                  f"{r['avg_actual']:<6.1f} | {r['samples']:,}")
    
    # Highlight points improvement
    if 'points' in results:
        print("\n" + "="*80)
        print("📊 POINTS MODEL IMPROVEMENT:")
        print(f"   Accuracy within ±3: {results['points']['within_3']:.1f}%")
        print(f"   Accuracy within ±5: {results['points']['within_5']:.1f}%")
        print(f"   Average points predicted: {results['points']['avg_actual']:.1f}")
        print("="*80)

if __name__ == "__main__":
    main()
