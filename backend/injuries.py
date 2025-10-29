"""
Enhanced Injury Analysis Module
Provides efficient, cached, and reliable injury data access.
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from dynamic_config import dynamic_config
from api_service import api_service

logger = logging.getLogger(__name__)

def get_nba_injury_report():
    """Fetch comprehensive NBA injury report with enhanced data processing."""
    return api_service.get_nba_injury_report()

def get_team_injuries(team_abbr):
    """Get injuries for a specific team."""
    return api_service.get_team_injuries(team_abbr)

def get_player_injury_status(player_name, team_abbr=None):
    """Get injury status for a specific player."""
    return api_service.get_player_injury_status(player_name, team_abbr)

def calculate_team_injury_impact(team_abbr):
    """Calculate overall injury impact for a team."""
    return api_service.calculate_team_injury_impact(team_abbr)

def get_injury_adjustment_factor(player_name, player_team, opponent_team):
    """Calculate injury adjustment factor for predictions."""
    return api_service.get_injury_adjustment_factor(player_name, player_team, opponent_team)

if __name__ == "__main__":
    # Test the injury system
    df = get_nba_injury_report()
    if df.empty:
        print("No injury data found.")
    else:
        print(f"Found {len(df)} injuries")
        print(df.head())