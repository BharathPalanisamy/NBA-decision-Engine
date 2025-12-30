"""Quick retrain of all models with new defensive feature"""
import pandas as pd
import xgboost as xgb
import pickle
from sklearn.model_selection import train_test_split

# Load features
df = pd.read_csv("data/processed/player_features.csv")

# Filter for recent games only
df = df[df["minutes"] >= 15].copy()

# Features to use
feature_cols = [col for col in df.columns if col.startswith("avg_") or 
                col in ["rest_days", "b2b", "pts_trend", "min_trend", 
                        "is_home", "pts_allowed"]]

# Train each stat
stats = {
    "points": "points_model_v2.pkl",
    "rebounds": "rebounds_model_v2.pkl", 
    "assists": "assists_model_v2.pkl",
    "steals": "steals_model_v2.pkl",
    "blocks": "blocks_model_v2.pkl",
    "fg3m": "fg3m_model_v2.pkl"
}

for stat, model_file in stats.items():
    print(f"\n{'='*50}")
    print(f"Training {stat}...")
    
    # Prepare data
    train_df = df.dropna(subset=feature_cols + [stat])
    X = train_df[feature_cols]
    y = train_df[stat]
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_preds = model.predict(X_train)
    test_preds = model.predict(X_test)
    
    # Calculate accuracy within ±3
    train_acc = (abs(train_preds - y_train) <= 3).mean() * 100
    test_acc = (abs(test_preds - y_test) <= 3).mean() * 100
    
    print(f"Train accuracy (±3): {train_acc:.1f}%")
    print(f"Test accuracy (±3): {test_acc:.1f}%")
    
    # Save
    with open(f"models/{model_file}", "wb") as f:
        pickle.dump(model, f)
    
    with open(f"models/{stat}_model_features.pkl", "wb") as f:
        pickle.dump(feature_cols, f)
    
    print(f"✅ Saved {model_file}")

print(f"\n{'='*50}")
print("🎯 All models retrained!")
