"""
NBA Player Performance Predictor - Streamlit App
Shows player stats and predicts next game performance
"""

import streamlit as st
import pandas as pd
import joblib
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="NBA Performance Predictor",
    page_icon="🏀",
    layout="wide"
)

@st.cache_data
def load_data():
    """Load player features data."""
    df = pd.read_csv('data/processed/player_features.csv')
    df['game_date'] = pd.to_datetime(df['game_date'])
    return df

@st.cache_resource
def load_models():
    """Load all trained models."""
    models = {}
    for stat in ['points', 'rebounds', 'assists', 'steals', 'blocks', 'fg3m']:
        try:
            models[stat] = {
                'model': joblib.load(f'models/{stat}_model_v2.pkl'),
                'features': joblib.load(f'models/{stat}_model_features.pkl')
            }
        except Exception as e:
            st.warning(f"Could not load {stat} model: {e}")
    return models

def engineer_features(df):
    """Add engineered features."""
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

def predict_next_game(player_data, models, opponent=None, is_home=True, rest_days=2):
    """Predict stats for next game based on latest rolling averages."""
    predictions = {}
    
    # Use the most recent game's features as baseline (first row since sorted descending)
    latest = player_data.iloc[0].copy()
    
    # Update context for next game
    latest['is_home'] = 1 if is_home else 0
    latest['rest_days'] = rest_days
    latest['is_b2b'] = 1 if rest_days <= 1 else 0
    
    for stat, model_info in models.items():
        try:
            features = model_info['features']
            available_features = [f for f in features if f in latest.index]
            
            if len(available_features) == len(features):
                X = latest[features].values.reshape(1, -1)
                pred = model_info['model'].predict(X)[0]
                predictions[stat] = max(0, round(pred, 1))
        except Exception as e:
            predictions[stat] = None
    
    return predictions

def main():
    st.title("🏀 NBA Player Performance Predictor")
    st.markdown("**Predict next game stats based on rolling averages and recent performance**")
    st.markdown("---")
    
    # Load data and models
    try:
        df = load_data()
        df = df[df['minutes'] >= 15].copy()  # Filter meaningful games
        df = engineer_features(df)
        models = load_models()
        
        if len(models) == 0:
            st.error("No models loaded. Please train models first.")
            return
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    # Sidebar - Player Selection
    st.sidebar.header("🎯 Select Player")
    
    # Get unique players sorted by recent activity
    recent_players = df.sort_values('game_date', ascending=False)['player_name'].unique()
    
    player_name = st.sidebar.selectbox(
        "Choose a player:",
        options=sorted(recent_players),
        index=0
    )
    
    # Filter data for selected player
    player_df = df[df['player_name'] == player_name].sort_values('game_date', ascending=False)
    
    if len(player_df) == 0:
        st.warning(f"No data found for {player_name}")
        return
    
    # Check if player has 2025-26 season games
    current_season_df = player_df[player_df['season'] == '2025-26'] if 'season' in player_df.columns else player_df
    
    if len(current_season_df) == 0:
        st.warning(f"⚠️ {player_name} hasn't played any games in the 2025-26 season yet.")
        return
    
    # Get latest game info for next prediction (most recent game)
    latest = current_season_df.iloc[0]
    is_home = latest.get('is_home', 1)
    rest_days = latest.get('rest_days', 2)
    opponent = None
    
    # Main content
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.subheader(f"📊 {player_name}")
        latest_game = current_season_df.iloc[0]
        st.metric("Last Game", latest_game['game_date'].strftime('%Y-%m-%d'))
        
    with col2:
        st.metric("Games Played (2025-26)", len(current_season_df))
        st.metric("Avg Minutes", f"{current_season_df['minutes'].mean():.1f}")
    
    with col3:
        st.metric("Season", "2025-26")
    
    # Recent Performance
    st.markdown("---")
    st.subheader("📈 Recent Performance (Last 10 Games - 2025-26 Season)")
    
    recent_games = current_season_df.head(10)  # Only 2025-26 games
    
    # Create performance chart
    fig = go.Figure()
    
    stats_to_plot = ['points', 'rebounds', 'assists']
    colors = {'points': '#1f77b4', 'rebounds': '#ff7f0e', 'assists': '#2ca02c'}
    
    for stat in stats_to_plot:
        if stat in recent_games.columns:
            fig.add_trace(go.Scatter(
                x=recent_games['game_date'],
                y=recent_games[stat],
                mode='lines+markers',
                name=stat.capitalize(),
                line=dict(color=colors[stat], width=3),
                marker=dict(size=8)
            ))
    
    fig.update_layout(
        title="Points, Rebounds, Assists - Last 10 Games",
        xaxis_title="Game Date",
        yaxis_title="Stats",
        height=400,
        hovermode='x unified',
        xaxis={'autorange': 'reversed'}  # Show most recent on right
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent games table
    recent_display = recent_games[['game_date', 'matchup', 'minutes', 'points', 'rebounds', 
                                    'assists', 'steals', 'blocks', 'fg3m']].head(5)
    recent_display['game_date'] = recent_display['game_date'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        recent_display.rename(columns={
            'game_date': 'Date',
            'matchup': 'Matchup',
            'minutes': 'MIN',
            'points': 'PTS',
            'rebounds': 'REB',
            'assists': 'AST',
            'steals': 'STL',
            'blocks': 'BLK',
            'fg3m': '3PM'
        }),
        hide_index=True,
        use_container_width=True
    )
    
    # Next Game Prediction
    st.markdown("---")
    st.subheader("🔮 Next Game Prediction")
    
    st.markdown("**Based on rolling averages and recent performance trends**")
    
    # Make prediction using ALL data (both seasons for accuracy)
    predictions = predict_next_game(player_df, models, opponent, is_home, rest_days)
    
    # Display predictions in metrics
    st.markdown("### 🎯 Next Game Prediction")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        pts = predictions.get('points', 0)
        avg_pts = current_season_df['points'].head(5).mean()
        delta_pts = pts - avg_pts
        st.metric("Points", f"{pts:.1f}", f"{delta_pts:+.1f} vs L5")
    
    with col2:
        reb = predictions.get('rebounds', 0)
        avg_reb = current_season_df['rebounds'].head(5).mean()
        delta_reb = reb - avg_reb
        st.metric("Rebounds", f"{reb:.1f}", f"{delta_reb:+.1f}")
    
    with col3:
        ast = predictions.get('assists', 0)
        avg_ast = current_season_df['assists'].head(5).mean()
        delta_ast = ast - avg_ast
        st.metric("Assists", f"{ast:.1f}", f"{delta_ast:+.1f}")
    
    with col4:
        stl = predictions.get('steals', 0)
        avg_stl = current_season_df['steals'].head(5).mean()
        delta_stl = stl - avg_stl
        st.metric("Steals", f"{stl:.1f}", f"{delta_stl:+.1f}")
    
    with col5:
        blk = predictions.get('blocks', 0)
        avg_blk = current_season_df['blocks'].head(5).mean()
        delta_blk = blk - avg_blk
        st.metric("Blocks", f"{blk:.1f}", f"{delta_blk:+.1f}")
    
    with col6:
        fg3 = predictions.get('fg3m', 0)
        avg_fg3 = current_season_df['fg3m'].head(5).mean()
        delta_fg3 = fg3 - avg_fg3
        st.metric("3-Pointers", f"{fg3:.1f}", f"{delta_fg3:+.1f}")
    
    # Rolling averages comparison
    st.markdown("---")
    st.subheader("📊 Rolling Averages (Current Season)")
    
    col1, col2, col3 = st.columns(3)
    
    latest = current_season_df.iloc[0]  # Most recent 2025-26 game
    
    with col1:
        st.markdown("**Last 3 Games**")
        st.write(f"Points: {latest.get('avg_points_3', 0):.1f}")
        st.write(f"Rebounds: {latest.get('avg_rebounds_3', 0):.1f}")
        st.write(f"Assists: {latest.get('avg_assists_3', 0):.1f}")
    
    with col2:
        st.markdown("**Last 5 Games**")
        st.write(f"Points: {latest.get('avg_points_5', 0):.1f}")
        st.write(f"Rebounds: {latest.get('avg_rebounds_5', 0):.1f}")
        st.write(f"Assists: {latest.get('avg_assists_5', 0):.1f}")
    
    with col3:
        st.markdown("**Last 10 Games**")
        st.write(f"Points: {latest.get('avg_points_10', 0):.1f}")
        st.write(f"Rebounds: {latest.get('avg_rebounds_10', 0):.1f}")
        st.write(f"Assists: {latest.get('avg_assists_10', 0):.1f}")
    
    # Model info
    st.markdown("---")
    st.markdown("**ℹ️ Model Info:** Trained on 2024-25 + 2025-26 seasons • Predictions use all historical data • Display shows current season only")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Model Performance")
    st.sidebar.markdown("- Points: 37.5% (±3)")
    st.sidebar.markdown("- Rebounds: 75.7% (±3)")
    st.sidebar.markdown("- Assists: 87.2% (±3)")
    st.sidebar.markdown("---")
    st.sidebar.markdown("*Predictions based on rolling averages, rest days, home/away, and momentum*")

if __name__ == "__main__":
    main()
