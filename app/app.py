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
    page_title="NBA Betting Predictor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .bet-card {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .over-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
    .under-card { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
    .neutral-card { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); }
    .hot-streak { color: #ff4444; font-weight: bold; }
    .cold-streak { color: #4444ff; font-weight: bold; }
    .big-number { font-size: 48px; font-weight: bold; }
    .confidence { font-size: 14px; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

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
    st.title("💰 NBA Betting Decision Engine")
    st.markdown("**Smart betting predictions powered by machine learning**")
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
    
    # Betting Lines Input
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Enter Betting Lines")
    st.sidebar.markdown("*Enter the sportsbook O/U for each stat*")
    
    line_points = st.sidebar.number_input("Points O/U", value=25.5, step=0.5)
    line_rebounds = st.sidebar.number_input("Rebounds O/U", value=7.5, step=0.5)
    line_assists = st.sidebar.number_input("Assists O/U", value=5.5, step=0.5)
    line_threes = st.sidebar.number_input("3-Pointers O/U", value=2.5, step=0.5)
    
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
    
    # Get latest game info
    latest = current_season_df.iloc[0]
    is_home = latest.get('is_home', 1)
    rest_days = latest.get('rest_days', 2)
    
    # Player Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📅 Last Game", latest['game_date'].strftime('%b %d'))
    with col2:
        st.metric("🏀 Games (2025-26)", len(current_season_df))
    with col3:
        avg_pts = current_season_df['points'].head(10).mean()
        st.metric("📈 Avg Points (L10)", f"{avg_pts:.1f}")
    with col4:
        # Hot/Cold indicator
        recent_3 = current_season_df['points'].head(3).mean()
        previous_7 = current_season_df['points'].iloc[3:10].mean() if len(current_season_df) > 10 else recent_3
        trend = "🔥 HOT" if recent_3 > previous_7 + 2 else "❄️ COLD" if recent_3 < previous_7 - 2 else "➡️ STABLE"
        st.metric("🌡️ Form", trend)
    
    # Make prediction
    predictions = predict_next_game(player_df, models, None, is_home, rest_days)
    
    # BETTING RECOMMENDATIONS
    st.markdown("---")
    st.header("🎯 BETTING RECOMMENDATIONS")
    
    def get_recommendation(prediction, line, recent_avg):
        diff = prediction - line
        confidence = abs(diff)
        
        if confidence >= 3:
            strength = "STRONG"
            color = "🟢"
        elif confidence >= 2:
            strength = "MODERATE"
            color = "🟡"
        else:
            strength = "WEAK"
            color = "🟠"
        
        if diff > 0:
            return f"OVER", diff, strength, color
        elif diff < 0:
            return f"UNDER", diff, strength, color
        else:
            return "SKIP", 0, "NO EDGE", "⚪"
    
    # Points Betting Card
    pts_pred = predictions.get('points', 0)
    pts_recent = current_season_df['points'].head(5).mean()
    pts_bet, pts_diff, pts_strength, pts_color = get_recommendation(pts_pred, line_points, pts_recent)
    
    st.markdown(f"""
    <div class="bet-card {'over-card' if pts_bet == 'OVER' else 'under-card' if pts_bet == 'UNDER' else 'neutral-card'}">
        <h2>🏀 POINTS</h2>
        <div class="big-number">{pts_pred:.1f}</div>
        <h3>Line: {line_points} → BET {pts_bet}</h3>
        <p class="confidence">{pts_color} {pts_strength} ({abs(pts_diff):.1f} point edge)</p>
        <p>Last 5 avg: {pts_recent:.1f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # Rebounds
    with col1:
        reb_pred = predictions.get('rebounds', 0)
        reb_recent = current_season_df['rebounds'].head(5).mean()
        reb_bet, reb_diff, reb_strength, reb_color = get_recommendation(reb_pred, line_rebounds, reb_recent)
        
        st.markdown(f"""
        <div class="bet-card {'over-card' if reb_bet == 'OVER' else 'under-card' if reb_bet == 'UNDER' else 'neutral-card'}">
            <h3>📦 REBOUNDS</h3>
            <div style="font-size: 32px; font-weight: bold;">{reb_pred:.1f}</div>
            <p><strong>Line: {line_rebounds} → {reb_bet}</strong></p>
            <p class="confidence">{reb_color} {reb_strength} ({abs(reb_diff):.1f})</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Assists
    with col2:
        ast_pred = predictions.get('assists', 0)
        ast_recent = current_season_df['assists'].head(5).mean()
        ast_bet, ast_diff, ast_strength, ast_color = get_recommendation(ast_pred, line_assists, ast_recent)
        
        st.markdown(f"""
        <div class="bet-card {'over-card' if ast_bet == 'OVER' else 'under-card' if ast_bet == 'UNDER' else 'neutral-card'}">
            <h3>🎯 ASSISTS</h3>
            <div style="font-size: 32px; font-weight: bold;">{ast_pred:.1f}</div>
            <p><strong>Line: {line_assists} → {ast_bet}</strong></p>
            <p class="confidence">{ast_color} {ast_strength} ({abs(ast_diff):.1f})</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 3-Pointers
    with col3:
        fg3_pred = predictions.get('fg3m', 0)
        fg3_recent = current_season_df['fg3m'].head(5).mean()
        fg3_bet, fg3_diff, fg3_strength, fg3_color = get_recommendation(fg3_pred, line_threes, fg3_recent)
        
        st.markdown(f"""
        <div class="bet-card {'over-card' if fg3_bet == 'OVER' else 'under-card' if fg3_bet == 'UNDER' else 'neutral-card'}">
            <h3>🎯 3-POINTERS</h3>
            <div style="font-size: 32px; font-weight: bold;">{fg3_pred:.1f}</div>
            <p><strong>Line: {line_threes} → {fg3_bet}</strong></p>
            <p class="confidence">{fg3_color} {fg3_strength} ({abs(fg3_diff):.1f})</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent Performance Chart
    st.markdown("---")
    st.subheader("📈 Recent Performance Trend")
    
    recent_games = current_season_df.head(10)
    
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
    st.subheader("📋 Last 5 Games")
    recent_display = recent_games[['game_date', 'matchup', 'minutes', 'points', 'rebounds', 
                                    'assists', 'steals', 'blocks', 'fg3m']].head(5)
    recent_display['game_date'] = recent_display['game_date'].dt.strftime('%m/%d')
    
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
    st.subheader("🔮 All Stat Predictions")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Points", f"{pts_pred:.1f}", f"{pts_pred - pts_recent:+.1f} vs L5")
    
    with col2:
        reb = predictions.get('rebounds', 0)
        avg_reb = current_season_df['rebounds'].head(5).mean()
        st.metric("Rebounds", f"{reb:.1f}", f"{reb - avg_reb:+.1f}")
    
    with col3:
        ast = predictions.get('assists', 0)
        avg_ast = current_season_df['assists'].head(5).mean()
        st.metric("Assists", f"{ast:.1f}", f"{ast - avg_ast:+.1f}")
    
    with col4:
        stl = predictions.get('steals', 0)
        avg_stl = current_season_df['steals'].head(5).mean()
        st.metric("Steals", f"{stl:.1f}", f"{stl - avg_stl:+.1f}")
    
    with col5:
        blk = predictions.get('blocks', 0)
        avg_blk = current_season_df['blocks'].head(5).mean()
        st.metric("Blocks", f"{blk:.1f}", f"{blk - avg_blk:+.1f}")
    
    with col6:
        fg3 = predictions.get('fg3m', 0)
        avg_fg3 = current_season_df['fg3m'].head(5).mean()
        st.metric("3-Pointers", f"{fg3:.1f}", f"{fg3 - avg_fg3:+.1f}")
    
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
    st.caption("💡 **How to use:** Enter sportsbook lines in sidebar → Check recommendations → Green STRONG bets have 3+ point edge")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Model Accuracy")
    st.sidebar.markdown("- Points: **38.4%** (±3)")
    st.sidebar.markdown("- Rebounds: 78.3% (±3)")
    st.sidebar.markdown("- Assists: 88.2% (±3)")
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Tip:** Look for STRONG bets (3+ point edge) and verify with recent form.")

if __name__ == "__main__":
    main()
