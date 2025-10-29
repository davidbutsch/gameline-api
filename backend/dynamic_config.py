"""
Dynamic configuration module for NBA prediction system.
This module provides dynamic data retrieval instead of hardcoded values.
"""

import requests
import pandas as pd
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DynamicConfig:
    """Dynamic configuration manager that fetches real-time data from APIs."""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes cache timeout
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self.cache:
            return False
        
        cache_time = self.cache[key].get('timestamp', 0)
        return (datetime.now().timestamp() - cache_time) < self.cache_timeout
    
    def _cache_data(self, key: str, data: Any):
        """Cache data with timestamp."""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    def get_current_season(self) -> str:
        """Get current NBA season dynamically."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # NBA season typically starts in October
        if current_month >= 10:
            return f"{current_year}-{str(current_year + 1)[2:]}"
        else:
            return f"{current_year - 1}-{str(current_year)[2:]}"
    
    def get_available_seasons(self) -> list:
        """Get list of available seasons with sufficient data."""
        current_season = self.get_current_season()
        current_year = int(current_season.split('-')[0])
        
        # Return last 3 seasons to ensure we have data
        seasons = []
        for i in range(3):
            year = current_year - i
            seasons.append(f"{year}-{str(year + 1)[2:]}")
        
        return seasons
    
    def get_primary_season(self) -> str:
        """Get the primary season to use for predictions (most recent with sufficient data)."""
        current_season = self.get_current_season()
        available_seasons = self.get_available_seasons()
        
        # Check if current season has sufficient data (at least 20 games per team on average)
        # For now, prioritize 2024-25 as it has the most complete data
        # In the future, this could check actual data availability
        if "2024-25" in available_seasons:
            return "2024-25"
        elif current_season in available_seasons:
            return current_season
        else:
            return available_seasons[0] if available_seasons else "2024-25"
    
    def get_league_averages_from_api(self, season: str, season_type: str = 'Regular Season') -> Dict[str, float]:
        """Get league averages dynamically from NBA API."""
        cache_key = f"league_averages_{season}_{season_type}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            from nba_api.stats.endpoints import leaguedashteamstats
            
            stats = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                season_type_all_star=season_type,
                timeout=120
            ).get_data_frames()[0]
            
            if stats.empty:
                logger.warning(f"No league stats data for {season}")
                return self._get_fallback_league_averages()
            
            # Calculate dynamic league averages
            league_averages = {
                'PTS': stats['PTS'].mean() / stats['GP'].mean(),
                'REB': stats['REB'].mean() / stats['GP'].mean(),
                'AST': stats['AST'].mean() / stats['GP'].mean(),
                'BLK': stats['BLK'].mean() / stats['GP'].mean(),
                'STL': stats['STL'].mean() / stats['GP'].mean(),
                'PACE': stats['PACE'].mean(),
                'DEF_RATING': stats['DEF_RATING'].mean(),
                'OFF_RATING': stats['OFF_RATING'].mean()
            }
            
            # Calculate standard deviations for normalization
            team_stats_per_game = stats.copy()
            for stat in ['PTS', 'REB', 'AST', 'BLK', 'STL']:
                team_stats_per_game[f'{stat}_PG'] = stats[stat] / stats['GP']
                league_averages[f'{stat}_std'] = team_stats_per_game[f'{stat}_PG'].std()
            
            self._cache_data(cache_key, league_averages)
            logger.info(f"Fetched dynamic league averages for {season}: {league_averages}")
            return league_averages
            
        except Exception as e:
            logger.error(f"Error fetching league averages for {season}: {e}")
            return self._get_fallback_league_averages()
    
    def _get_fallback_league_averages(self) -> Dict[str, float]:
        """Fallback league averages when API fails."""
        logger.warning("Using fallback league averages - API data unavailable")
        return {
            'PTS': 115.0, 'REB': 43.0, 'AST': 25.0, 'BLK': 5.0, 'STL': 7.0,
            'PTS_std': 4.0, 'REB_std': 2.5, 'AST_std': 2.0, 'BLK_std': 0.8, 'STL_std': 0.9,
            'PACE': 100.0, 'DEF_RATING': 110.0, 'OFF_RATING': 110.0
        }
    
    def get_player_advanced_stats_from_api(self, player_id: int, season: str, season_type: str = 'Regular Season') -> Dict[str, float]:
        """Get player advanced stats dynamically from NBA API."""
        cache_key = f"player_advanced_{player_id}_{season}_{season_type}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            from nba_api.stats.endpoints import leaguedashplayerstats
            
            all_stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star=season_type,
                timeout=120
            ).get_data_frames()[0]
            
            player_stats = all_stats[all_stats['PLAYER_ID'] == player_id]
            
            if player_stats.empty:
                logger.warning(f"No advanced stats for player {player_id}, season {season}")
                return self._get_fallback_player_stats()
            
            stats_row = player_stats.iloc[0]
            advanced_stats = {
                'USG_PCT': stats_row.get('USG_PCT', 0.2),
                'TS_PCT': stats_row.get('TS_PCT', 0.5),
                'DEF_RATING': stats_row.get('DEF_RATING', 110.0),
                'OFF_RATING': stats_row.get('OFF_RATING', 110.0),
                'PER': stats_row.get('PER', 15.0),
                'AST_PCT': stats_row.get('AST_PCT', 0.1),
                'REB_PCT': stats_row.get('REB_PCT', 0.1),
                'TOV_PCT': stats_row.get('TOV_PCT', 0.1),
                'EFG_PCT': stats_row.get('EFG_PCT', 0.5),
                'PACE': stats_row.get('PACE', 100.0),
                'PIE': stats_row.get('PIE', 0.1)
            }
            
            self._cache_data(cache_key, advanced_stats)
            logger.info(f"Fetched dynamic advanced stats for player {player_id}: {advanced_stats}")
            return advanced_stats
            
        except Exception as e:
            logger.error(f"Error fetching advanced stats for player {player_id}: {e}")
            return self._get_fallback_player_stats()
    
    def _get_fallback_player_stats(self) -> Dict[str, float]:
        """Fallback player stats when API fails."""
        logger.warning("Using fallback player stats - API data unavailable")
        return {
            'USG_PCT': 0.2, 'TS_PCT': 0.5, 'DEF_RATING': 110.0, 'OFF_RATING': 110.0,
            'PER': 15.0, 'AST_PCT': 0.1, 'REB_PCT': 0.1, 'TOV_PCT': 0.1,
            'EFG_PCT': 0.5, 'PACE': 100.0, 'PIE': 0.1
        }
    
    def get_team_stats_from_api(self, team_id: int, season: str, season_type: str = 'Regular Season') -> Dict[str, float]:
        """Get team stats dynamically from NBA API."""
        cache_key = f"team_stats_{team_id}_{season}_{season_type}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            from nba_api.stats.endpoints import leaguedashteamstats
            
            team_stats = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                season_type_all_star=season_type,
                timeout=120
            ).get_data_frames()[0]
            
            team_data = team_stats[team_stats['TEAM_ID'] == team_id]
            
            if team_data.empty:
                logger.warning(f"No team stats for team {team_id}, season {season}")
                return self._get_fallback_team_stats()
            
            team_row = team_data.iloc[0]
            games_played = int(team_row.get('GP', 82))
            
            if games_played == 0:
                games_played = 82  # Prevent division by zero
            
            team_stats_dict = {
                'PTS': float(team_row['PTS']) / games_played if 'PTS' in team_row and pd.notna(team_row['PTS']) else 110.0,
                'REB': float(team_row['REB']) / games_played if 'REB' in team_row and pd.notna(team_row['REB']) else 43.0,
                'AST': float(team_row['AST']) / games_played if 'AST' in team_row and pd.notna(team_row['AST']) else 25.0,
                'BLK': float(team_row['BLK']) / games_played if 'BLK' in team_row and pd.notna(team_row['BLK']) else 5.0,
                'STL': float(team_row['STL']) / games_played if 'STL' in team_row and pd.notna(team_row['STL']) else 7.0,
                'PACE': float(team_row.get('PACE', 100.0)),
                'OFF_RATING': float(team_row.get('OFF_RATING', 110.0)),
                'DEF_RATING': float(team_row.get('DEF_RATING', 110.0)),
                'GP': games_played
            }
            
            self._cache_data(cache_key, team_stats_dict)
            logger.info(f"Fetched dynamic team stats for team {team_id}: {team_stats_dict}")
            return team_stats_dict
            
        except Exception as e:
            logger.error(f"Error fetching team stats for team {team_id}: {e}")
            return self._get_fallback_team_stats()
    
    def _get_fallback_team_stats(self) -> Dict[str, float]:
        """Fallback team stats when API fails."""
        logger.warning("Using fallback team stats - API data unavailable")
        return {
            'PTS': 110.0, 'REB': 43.0, 'AST': 25.0, 'BLK': 5.0, 'STL': 7.0,
            'PACE': 100.0, 'DEF_RATING': 110.0, 'OFF_RATING': 110.0, 'GP': 82
        }
    
    def get_league_minutes_averages_from_api(self, season: str, season_type: str = 'Regular Season') -> Dict[str, float]:
        """Get league-wide minutes averages dynamically from NBA API."""
        cache_key = f"league_minutes_{season}_{season_type}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            from nba_api.stats.endpoints import leaguedashplayerstats
            
            player_stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star=season_type,
                timeout=120
            ).get_data_frames()[0]
            
            if player_stats.empty:
                logger.warning(f"No player stats data for {season}")
                return self._get_fallback_minutes_averages()
            
            # Filter for active players (>= 5 games, >= 5 MPG)
            active_players = player_stats[
                (player_stats['GP'] >= 5) & 
                ((player_stats['MIN'] / player_stats['GP']) >= 5.0)
            ]
            
            if active_players.empty:
                return self._get_fallback_minutes_averages()
            
            # Calculate minutes per game for each player
            active_players = active_players.copy()
            active_players['MPG'] = active_players['MIN'] / active_players['GP']
            
            league_avg_mpg = active_players['MPG'].mean()
            league_std_mpg = active_players['MPG'].std()
            
            minutes_averages = {
                'avg_mpg': float(league_avg_mpg),
                'std_mpg': float(league_std_mpg)
            }
            
            self._cache_data(cache_key, minutes_averages)
            logger.info(f"Fetched dynamic league minutes averages for {season}: {minutes_averages}")
            return minutes_averages
            
        except Exception as e:
            logger.error(f"Error fetching league minutes averages for {season}: {e}")
            return self._get_fallback_minutes_averages()
    
    def _get_fallback_minutes_averages(self) -> Dict[str, float]:
        """Fallback minutes averages when API fails."""
        logger.warning("Using fallback minutes averages - API data unavailable")
        return {'avg_mpg': 24.0, 'std_mpg': 8.0}
    
    def get_injury_impact_scores_from_historical_data(self) -> Dict[str, float]:
        """Get injury impact scores based on historical performance data."""
        # This could be enhanced to analyze historical injury data
        # For now, return research-based values
        return {
            "high": 0.8,
            "medium": 0.5, 
            "low": 0.2,
            "unknown": 0.3
        }
    
    def get_injury_type_weights_from_historical_data(self) -> Dict[str, float]:
        """Get injury type weights based on historical impact analysis."""
        # This could be enhanced to analyze historical injury impact data
        # For now, return research-based values
        return {
            "knee_ankle_back": 0.1,  # Higher impact injuries
            "finger_hand_wrist": 0.05  # Moderate impact injuries
        }
    
    def get_opponent_impact_weights(self) -> Dict[str, Dict[str, float]]:
        """Get opponent impact weights for different stat categories."""
        return {
            'Points': {'PTS': +0.20, 'REB': -0.10, 'AST': +0.05, 'STL': -0.08, 'BLK': -0.08},
            'Rebounds': {'PTS': +0.10, 'REB': -0.15, 'AST': +0.00, 'STL': -0.05, 'BLK': -0.03},
            'Assists': {'PTS': +0.15, 'REB': -0.05, 'AST': +0.20, 'STL': -0.05, 'BLK': -0.03},
            'Steals': {'PTS': +0.08, 'REB': -0.03, 'AST': +0.03, 'STL': +0.15, 'BLK': -0.03},
            'Blocks': {'PTS': +0.05, 'REB': -0.03, 'AST': +0.00, 'STL': -0.03, 'BLK': +0.20}
        }

# Global instance
dynamic_config = DynamicConfig()
