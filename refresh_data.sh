#!/bin/bash
# Refresh NBA Decision Engine with latest data

echo "🔄 Starting data refresh for NBA Decision Engine..."
echo ""

# Activate virtual environment
source .venv/bin/activate

# Step 1: Pull latest game logs
echo "📥 Step 1/6: Pulling latest game logs from NBA API..."
python etl/pull_gamelogs.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to pull game logs"
    exit 1
fi
echo ""

# Step 2: Load to PostgreSQL
echo "💾 Step 2/6: Loading data to PostgreSQL..."
python etl/load_to_postgres.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to load data to PostgreSQL"
    exit 1
fi
echo ""

# Step 3: Build features
echo "🔧 Step 3/6: Building features..."
python features/build_features.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to build features"
    exit 1
fi
echo ""

# Step 4-5: Train all models
echo "🤖 Step 4/6: Training betting prop models..."
python models/train_all_models.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to train models"
    exit 1
fi
echo ""

# Step 6: Generate predictions
echo "🎲 Step 5/6: Generating betting props predictions..."
python models/predict_betting_props.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to generate predictions"
    exit 1
fi
echo ""

echo "✅ Data refresh complete!"
echo "🚀 You can now run the Streamlit app with: streamlit run app/fantasy_app.py"
