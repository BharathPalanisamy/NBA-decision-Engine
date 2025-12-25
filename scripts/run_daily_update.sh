#!/bin/bash

# NBA Betting Engine - Automated Daily Update
# Run this script every day at 6 AM to update predictions

cd /Users/bharathpalanisamy/nba-decision-engine

echo "Starting daily NBA data update..."
python etl/update_daily.py

echo "Update complete! Streamlit app will automatically reload."
