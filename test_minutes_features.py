#!/usr/bin/env python3
"""
Test script to demonstrate the impact of new minutes-based features on NBA player predictions.
"""

import logging
from predictive_model import AdvancedNBAPlayerPredictor
import bet_calculations as bc

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_minutes_features():
    """Test how minutes-related features affect predictions."""
    
    print("=== Minutes Feature Impact Analysis ===\n")
    
    # Test players with different minute patterns
    test_players = [
        'LeBron James',    # High minutes veteran
        'Jayson Tatum',    # Star player with normal minutes
        'Scottie Barnes'   # Younger player with variable minutes
    ]
    
    predictor = AdvancedNBAPlayerPredictor()
    
    for player_name in test_players:
        print(f"Testing: {player_name}")
        print("-" * 40)
        
        try:
            # Get player ID
            player_info = bc.get_player_id(player_name)
            if not player_info:
                print(f"  Player {player_name} not found\n")
                continue
                
            player_id = player_info['player_id']
            
            # Get player's recent game data
            all_games = predictor.prepare_data(player_id, seasons=['2024-25'], season_type='Regular Season')
            if all_games.empty:
                print(f"  No game data for {player_name}\n")
                continue
                
            all_games['Player_ID'] = player_id
            
            # Analyze minutes patterns
            recent_mins = all_games['MIN'].head(10).mean()
            season_mins = all_games['MIN'].mean()
            max_mins = all_games['MIN'].max()
            min_mins = all_games['MIN'].min()
            
            print(f"  Minutes Analysis:")
            print(f"    Season Average: {season_mins:.1f} MPG")
            print(f"    Recent 10 Games: {recent_mins:.1f} MPG")
            print(f"    Range: {min_mins:.0f} - {max_mins:.0f} minutes")
            
            # Get league averages for comparison
            league_min_stats = bc.get_league_average_minutes('2024-25', 'Regular Season')
            league_avg = league_min_stats['avg_mpg']
            league_std = league_min_stats['std_mpg']
            
            # Calculate z-score vs league
            min_zscore = (season_mins - league_avg) / league_std
            print(f"    vs League Average: {min_zscore:+.2f} std devs")
            
            # Test feature creation
            features = predictor.create_features(all_games, 'BOS', 'Regular Season')
            
            # Show minutes-related features
            min_features = [col for col in predictor.feature_cols if 'min' in col.lower()]
            print(f"  Minutes Features Created: {len(min_features)}")
            for feat in min_features:
                print(f"    - {feat}")
            
            # Get fatigue metrics
            fatigue = bc.get_player_fatigue_metrics(player_id, '2024-25', 'Regular Season')
            print(f"  Fatigue Indicators:")
            print(f"    Average Minutes: {fatigue['AVG_MIN']:.1f}")
            print(f"    Average Rest Days: {fatigue['AVG_REST_DAYS']:.1f}")
            
            # Determine player archetype based on minutes
            if season_mins > league_avg + league_std:
                archetype = "Heavy Usage Star"
            elif season_mins > league_avg:
                archetype = "Regular Starter"
            elif season_mins > league_avg - league_std:
                archetype = "Role Player"
            else:
                archetype = "Bench Player"
                
            print(f"  Player Archetype: {archetype}")
            print()
            
        except Exception as e:
            print(f"  Error processing {player_name}: {e}")
            print()

def show_minutes_feature_impact():
    """Show how minutes features theoretically impact different stat predictions."""
    
    print("=== Minutes Feature Impact on Predictions ===\n")
    
    scenarios = [
        {
            'name': 'High Minutes Player (38+ MPG)',
            'avg_min': 38.5,
            'league_avg': 24.0,
            'recent_trend': 0.05,  # 5% increase recently
            'fatigue_risk': 'High'
        },
        {
            'name': 'Normal Starter (32-35 MPG)',
            'avg_min': 33.0,
            'league_avg': 24.0,
            'recent_trend': 0.0,   # Stable
            'fatigue_risk': 'Medium'
        },
        {
            'name': 'Role Player (18-25 MPG)',
            'avg_min': 22.0,
            'league_avg': 24.0,
            'recent_trend': -0.03, # 3% decrease recently
            'fatigue_risk': 'Low'
        }
    ]
    
    for scenario in scenarios:
        print(f"{scenario['name']}:")
        print(f"  Average Minutes: {scenario['avg_min']} MPG")
        
        # Calculate theoretical feature values
        min_vs_league = (scenario['avg_min'] - scenario['league_avg']) / 8.0  # Assume 8.0 std dev
        min_trend = scenario['recent_trend']
        
        print(f"  Minutes vs League: {min_vs_league:+.2f} std devs")
        print(f"  Recent Trend: {min_trend:+.1%}")
        print(f"  Fatigue Risk: {scenario['fatigue_risk']}")
        
        # Theoretical impact on predictions
        if scenario['avg_min'] > 35:
            pts_impact = "+Higher volume, but fatigue risk"
            efficiency_impact = "May decrease in late games"
        elif scenario['avg_min'] > 28:
            pts_impact = "+Consistent opportunity"
            efficiency_impact = "Stable performance expected"
        else:
            pts_impact = "Limited by playing time"
            efficiency_impact = "Higher per-minute efficiency"
            
        print(f"  Expected Impact on Points: {pts_impact}")
        print(f"  Efficiency Expectation: {efficiency_impact}")
        print()

if __name__ == "__main__":
    test_minutes_features()
    show_minutes_feature_impact()
    
    print("=== Summary ===")
    print("New minutes-based features added to the predictive model:")
    print("1. MIN - Raw minutes played in each game")
    print("2. min_usage_interaction - Minutes × Usage Rate interaction")
    print("3. high_min_fatigue - Binary flag for high minute games (>35 min)")
    print("4. PTS_per_min - Points per minute efficiency")
    print("5. min_trend - Recent minutes trend vs season average")
    print()
    print("These features help the model account for:")
    print("- Player workload and fatigue")
    print("- Opportunity (more minutes = more chances for stats)")
    print("- Efficiency patterns at different minute levels")
    print("- Recent coaching decisions and role changes")
    print("- Usage rate interactions with playing time")
