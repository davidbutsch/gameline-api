"""
Enhanced API Service Layer
Provides efficient, cached, and reliable API access with error handling and monitoring.
"""

import requests
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
from functools import wraps
from api_config import api_config
from dynamic_config import dynamic_config

logger = logging.getLogger(__name__)

class APIService:
    """Enhanced API service with caching, rate limiting, and error handling."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        self.cache = {}
        self.rate_limit_tracker = {}
        self.error_counts = {}
        self.performance_metrics = {}
    
    def rate_limit(self, endpoint: str):
        """Apply rate limiting to prevent API overload."""
        now = time.time()
        if endpoint in self.rate_limit_tracker:
            time_since_last = now - self.rate_limit_tracker[endpoint]
            if time_since_last < api_config.rate_limit_delay:
                time.sleep(api_config.rate_limit_delay - time_since_last)
        self.rate_limit_tracker[endpoint] = now
    
    def handle_api_error(self, endpoint: str, error: Exception) -> bool:
        """Handle API errors with exponential backoff."""
        if endpoint not in self.error_counts:
            self.error_counts[endpoint] = 0
        
        self.error_counts[endpoint] += 1
        
        if self.error_counts[endpoint] >= api_config.max_retries:
            logger.error(f"Max retries exceeded for {endpoint}: {error}")
            return False
        
        # Exponential backoff
        delay = 2 ** self.error_counts[endpoint]
        logger.warning(f"API error for {endpoint}, retrying in {delay}s: {error}")
        time.sleep(delay)
        return True
    
    def get_with_retry(self, url: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Get data with retry logic and error handling."""
        self.rate_limit(endpoint)
        
        for attempt in range(api_config.max_retries):
            try:
                start_time = time.time()
                response = self.session.get(url, timeout=api_config.api_timeout, **kwargs)
                
                # Track performance
                duration = time.time() - start_time
                if endpoint not in self.performance_metrics:
                    self.performance_metrics[endpoint] = []
                self.performance_metrics[endpoint].append(duration)
                
                if response.status_code == 200:
                    self.error_counts[endpoint] = 0  # Reset error count on success
                    return response
                else:
                    logger.warning(f"API returned status {response.status_code} for {endpoint}")
                    
            except Exception as e:
                if not self.handle_api_error(endpoint, e):
                    return None
        
        return None
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get data from cache if valid."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if api_config.is_cache_valid(timestamp):
                logger.debug(f"Cache hit for {key}")
                return data
            else:
                del self.cache[key]
        return None
    
    def set_cached_data(self, key: str, data: Any):
        """Set data in cache with timestamp."""
        self.cache[key] = (data, datetime.now().timestamp())
        logger.debug(f"Cache set for {key}")
    
    def get_nba_injury_report(self) -> pd.DataFrame:
        """Get NBA injury report with caching and error handling."""
        cache_key = "nba_injury_report"
        cached_data = self.get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            response = self.get_with_retry(api_config.espn_injury_api, "injury_report")
            if not response:
                logger.error("Failed to fetch injury report after retries")
                return pd.DataFrame()
            
            data = response.json()
            all_injuries = []
            
            for team in data.get("injuries", []):
                team_name = team.get("displayName")
                team_abbr = api_config.get_team_abbreviation(team_name)
                
                for injury in team.get("injuries", []):
                    athlete = injury.get("athlete", {})
                    injury_data = {
                        "player_name": athlete.get("displayName"),
                        "team_name": team_name,
                        "team_abbr": team_abbr,
                        "status": injury.get("status"),
                        "short_comment": injury.get("shortComment"),
                        "long_comment": injury.get("longComment"),
                        "return_date": injury.get("date"),
                        "injury_type": injury.get("type"),
                        "severity": self._classify_injury_severity(injury.get("status"), injury.get("shortComment", "")),
                        "impact_score": self._calculate_injury_impact(injury.get("status"), injury.get("shortComment", ""))
                    }
                    all_injuries.append(injury_data)
            
            df = pd.DataFrame(all_injuries)
            self.set_cached_data(cache_key, df)
            logger.info(f"Fetched {len(df)} injuries from ESPN API")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching injury report: {e}")
            return pd.DataFrame()
    
    def _classify_injury_severity(self, status: str, comment: str) -> str:
        """Classify injury severity based on status and comments."""
        status_lower = status.lower() if status else ""
        comment_lower = comment.lower() if comment else ""
        
        if any(keyword in status_lower for keyword in ["out", "doubtful"]):
            return "high"
        elif any(keyword in status_lower for keyword in ["questionable", "probable"]):
            return "medium"
        elif any(keyword in status_lower for keyword in ["active", "available"]):
            return "low"
        
        return "unknown"
    
    def _calculate_injury_impact(self, status: str, comment: str) -> float:
        """Calculate numerical impact score for injuries (0-1 scale)."""
        severity = self._classify_injury_severity(status, comment)
        
        # Get dynamic impact scores
        impact_scores = dynamic_config.get_injury_impact_scores_from_historical_data()
        base_score = impact_scores.get(severity, 0.3)
        
        # Get dynamic injury type weights
        injury_weights = dynamic_config.get_injury_type_weights_from_historical_data()
        
        # Adjust based on specific injury types
        comment_lower = comment.lower() if comment else ""
        if any(keyword in comment_lower for keyword in ["knee", "ankle", "back"]):
            base_score += injury_weights.get("knee_ankle_back", 0.1)
        elif any(keyword in comment_lower for keyword in ["finger", "hand", "wrist"]):
            base_score += injury_weights.get("finger_hand_wrist", 0.05)
        
        return min(1.0, base_score)
    
    def get_team_injuries(self, team_abbr: str) -> pd.DataFrame:
        """Get injuries for a specific team."""
        df = self.get_nba_injury_report()
        if df.empty:
            return pd.DataFrame()
        
        return df[df['team_abbr'] == team_abbr.upper()]
    
    def calculate_team_injury_impact(self, team_abbr: str) -> float:
        """Calculate overall injury impact for a team."""
        team_injuries = self.get_team_injuries(team_abbr)
        if team_injuries.empty:
            return 0.0
        
        # Weight by player importance and injury severity
        total_impact = 0.0
        for _, injury in team_injuries.iterrows():
            impact_score = injury.get('impact_score', 0.0)
            # Weight by severity
            severity_weight = {
                'high': 1.0,
                'medium': 0.7,
                'low': 0.3,
                'unknown': 0.5
            }.get(injury.get('severity', 'unknown'), 0.5)
            
            total_impact += impact_score * severity_weight
        
        # Normalize by number of injuries
        return min(1.0, total_impact / len(team_injuries))
    
    def get_player_injury_status(self, player_name: str, team_abbr: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get injury status for a specific player."""
        df = self.get_nba_injury_report()
        if df.empty:
            return None
        
        # Try exact match first
        player_injuries = df[df['player_name'] == player_name]
        
        if not player_injuries.empty:
            return player_injuries.iloc[0].to_dict()
        
        # Try fuzzy matching if no exact match
        if team_abbr:
            team_injuries = df[df['team_abbr'] == team_abbr.upper()]
            for _, injury in team_injuries.iterrows():
                if player_name.lower() in injury['player_name'].lower():
                    return injury.to_dict()
        
        return None
    
    def get_injury_adjustment_factor(self, player_name: str, player_team: str, opponent_team: str) -> float:
        """Calculate injury adjustment factor for predictions."""
        try:
            # Get player injury status
            player_injury = self.get_player_injury_status(player_name, player_team)
            
            # Get team injury impacts
            player_team_impact = self.calculate_team_injury_impact(player_team)
            opponent_team_impact = self.calculate_team_injury_impact(opponent_team)
            
            # Calculate net adjustment
            if player_injury:
                player_impact = player_injury.get('impact_score', 0.0)
            else:
                player_impact = 0.0
            
            # Net adjustment: positive if opponent is more injured, negative if player's team is more injured
            net_adjustment = (opponent_team_impact - player_team_impact) * 0.1 + (player_impact * 0.05)
            
            return max(-0.2, min(0.2, net_adjustment))  # Cap between -20% and +20%
            
        except Exception as e:
            logger.error(f"Error calculating injury adjustment: {e}")
            return 0.0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics."""
        metrics = {}
        for endpoint, times in self.performance_metrics.items():
            if times:
                metrics[endpoint] = {
                    'avg_response_time': sum(times) / len(times),
                    'max_response_time': max(times),
                    'min_response_time': min(times),
                    'total_calls': len(times)
                }
        return metrics
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cache cleared")

# Global API service instance
api_service = APIService()
