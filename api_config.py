"""
API Configuration and Constants Management
Centralized configuration for all API endpoints, timeouts, and dynamic values.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class APIConfig:
    """Centralized API configuration management."""
    
    def __init__(self):
        self.cache_timeout = int(os.getenv('CACHE_TIMEOUT', '300'))  # 5 minutes
        self.api_timeout = int(os.getenv('API_TIMEOUT', '120'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', '0.1'))
        
        # NBA API endpoints
        self.nba_api_base = "https://stats.nba.com/stats"
        self.espn_injury_api = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
        
        # Performance thresholds
        self.min_games_for_prediction = int(os.getenv('MIN_GAMES', '5'))
        self.max_games_for_analysis = int(os.getenv('MAX_GAMES', '100'))
        self.recency_weight_lambda = float(os.getenv('RECENCY_LAMBDA', '0.0231'))  # -ln(0.5)/30
        
        # Model parameters
        self.model_params = {
            'random_forest': {
                'n_estimators': int(os.getenv('RF_ESTIMATORS', '100')),
                'max_depth': int(os.getenv('RF_MAX_DEPTH', '10')),
                'min_samples_split': int(os.getenv('RF_MIN_SAMPLES', '5')),
                'random_state': 42
            },
            'gradient_boosting': {
                'n_estimators': int(os.getenv('GB_ESTIMATORS', '100')),
                'max_depth': int(os.getenv('GB_MAX_DEPTH', '5')),
                'learning_rate': float(os.getenv('GB_LEARNING_RATE', '0.1')),
                'random_state': 42
            },
            'extra_trees': {
                'n_estimators': int(os.getenv('ET_ESTIMATORS', '100')),
                'max_depth': int(os.getenv('ET_MAX_DEPTH', '10')),
                'min_samples_split': int(os.getenv('ET_MIN_SAMPLES', '5')),
                'random_state': 42
            },
            'xgboost': {
                'n_estimators': int(os.getenv('XGB_ESTIMATORS', '100')),
                'max_depth': int(os.getenv('XGB_MAX_DEPTH', '5')),
                'learning_rate': float(os.getenv('XGB_LEARNING_RATE', '0.1')),
                'random_state': 42,
                'verbosity': 0
            },
            'lightgbm': {
                'n_estimators': int(os.getenv('LGBM_ESTIMATORS', '100')),
                'max_depth': int(os.getenv('LGBM_MAX_DEPTH', '5')),
                'learning_rate': float(os.getenv('LGBM_LEARNING_RATE', '0.1')),
                'random_state': 42,
                'verbose': -1
            }
        }
        
        # Dynamic thresholds based on league data
        self.dynamic_thresholds = {
            'min_minutes': 10.0,
            'max_points': 50.0,
            'fatigue_threshold_minutes': 38.0,
            'fatigue_threshold_rest': 1.0,
            'variance_threshold': 0.01,
            'max_opponent_impact': 0.2
        }
        
        # Team mapping for injury API
        self.team_abbreviations = {
            'Atlanta Hawks': 'ATL',
            'Boston Celtics': 'BOS', 
            'Brooklyn Nets': 'BKN',
            'Charlotte Hornets': 'CHA',
            'Chicago Bulls': 'CHI',
            'Cleveland Cavaliers': 'CLE',
            'Dallas Mavericks': 'DAL',
            'Denver Nuggets': 'DEN',
            'Detroit Pistons': 'DET',
            'Golden State Warriors': 'GSW',
            'Houston Rockets': 'HOU',
            'Indiana Pacers': 'IND',
            'Los Angeles Clippers': 'LAC',
            'Los Angeles Lakers': 'LAL',
            'Memphis Grizzlies': 'MEM',
            'Miami Heat': 'MIA',
            'Milwaukee Bucks': 'MIL',
            'Minnesota Timberwolves': 'MIN',
            'New Orleans Pelicans': 'NOP',
            'New York Knicks': 'NYK',
            'Oklahoma City Thunder': 'OKC',
            'Orlando Magic': 'ORL',
            'Philadelphia 76ers': 'PHI',
            'Phoenix Suns': 'PHX',
            'Portland Trail Blazers': 'POR',
            'Sacramento Kings': 'SAC',
            'San Antonio Spurs': 'SAS',
            'Toronto Raptors': 'TOR',
            'Utah Jazz': 'UTA',
            'Washington Wizards': 'WAS'
        }
    
    def get_dynamic_thresholds(self, league_stats: Dict[str, float]) -> Dict[str, float]:
        """Get dynamic thresholds based on current league statistics."""
        if not league_stats:
            return self.dynamic_thresholds
            
        # Calculate dynamic thresholds based on league averages
        pts_avg = league_stats.get('PTS', 115.0)
        min_avg = league_stats.get('MIN', 24.0)
        
        return {
            'min_minutes': max(5.0, min_avg * 0.4),  # 40% of league average
            'max_points': min(60.0, pts_avg * 1.5),   # 150% of league average
            'fatigue_threshold_minutes': min_avg * 1.6,  # 160% of league average
            'fatigue_threshold_rest': 1.0,
            'variance_threshold': 0.01
        }
    
    def get_model_params(self, model_type: str) -> Dict[str, Any]:
        """Get model parameters for a specific model type."""
        return self.model_params.get(model_type, {})
    
    def get_team_abbreviation(self, team_name: str) -> str:
        """Get team abbreviation from full team name."""
        return self.team_abbreviations.get(team_name, "")
    
    def is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached data is still valid."""
        return (datetime.now().timestamp() - timestamp) < self.cache_timeout

# Global configuration instance
api_config = APIConfig()
