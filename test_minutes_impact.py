#!/usr/bin/env python3
"""Test script to demonstrate how minutes per game affects predictions."""

import logging
from predictive_model import AdvancedNBAPlayerPredictor
import bet_calculations as bc

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_minutes_impact():
    """Test how minutes per game impacts player performance predictions."""
    
    print("=== Minutes Per Game Impact Analysis ===\n")
    
    # Get a player to test
    player_info = bc.get_player_id('Anthony Davis')
    if not player_info:
        print("Player not found")
        return
        
    player_id = player_info['player_id']
    print(f"Testing with Anthony Davis (ID: {player_id})")
    
    try:
        # Get player data
        predictor = AdvancedNBAPlayerPredictor()
        all_games = predictor.prepare_data(player_id, ['2024-25'], 'Regular Season')
        
        if all_games.empty:
            print("No game data available")
            return
            
        print(f"Found {len(all_games)} games")
        
        # Analyze minutes vs performance correlation
        if 'MIN' in all_games.columns and len(all_games) > 5:
            print(f"\n--- Minutes vs Performance Analysis ---")
            
            # Calculate correlations
            for stat in ['PTS', 'REB', 'AST', 'BLK', 'STL']:
                if stat in all_games.columns:
                    corr = all_games['MIN'].corr(all_games[stat])
                    print(f"Minutes vs {stat} correlation: {corr:.3f}")
            
            # Show efficiency metrics
            print(f"\n--- Per-Minute Efficiency ---")
            for stat in ['PTS', 'REB', 'AST']:
                per_min_col = f'{stat}_per_min'
                if per_min_col in all_games.columns:
                    avg_efficiency = all_games[per_min_col].mean()
                    per_36 = avg_efficiency * 36
                    print(f"{stat} per 36 minutes: {per_36:.1f}")
            
            # Show minutes distribution
            print(f"\n--- Minutes Distribution ---")
            print(f"Average minutes: {all_games['MIN'].mean():.1f}")
            print(f"Min minutes: {all_games['MIN'].min()}")
            print(f"Max minutes: {all_games['MIN'].max()}")
            print(f"Standard deviation: {all_games['MIN'].std():.1f}")
            
            # Show games by minutes range
            high_min_games = all_games[all_games['MIN'] >= 35]
            low_min_games = all_games[all_games['MIN'] <= 25]
            
            if len(high_min_games) > 0 and len(low_min_games) > 0:
                print(f"\n--- Performance by Minutes Played ---")
                print(f"High minutes games (35+): {len(high_min_games)}")
                print(f"  Average PTS: {high_min_games['PTS'].mean():.1f}")
                print(f"  Average REB: {high_min_games['REB'].mean():.1f}")
                print(f"  Average AST: {high_min_games['AST'].mean():.1f}")
                
                print(f"Low minutes games (25-): {len(low_min_games)}")
                print(f"  Average PTS: {low_min_games['PTS'].mean():.1f}")
                print(f"  Average REB: {low_min_games['REB'].mean():.1f}")
                print(f"  Average AST: {low_min_games['AST'].mean():.1f}")
            
            # Show fatigue metrics if available
            if 'min_trend' in all_games.columns:
                print(f"\n--- Minutes Trend Analysis ---")
                recent_trend = all_games['min_trend'].tail(5).mean()
                print(f"Recent minutes trend: {recent_trend:+.1f}")
                
            if 'min_consistency' in all_games.columns:
                print(f"Minutes consistency: {all_games['min_consistency'].mean():.3f}")
        
        else:
            print("Insufficient data for minutes analysis")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def show_minutes_features():
    """Show what minutes-related features are available."""
    
    print("\n=== Available Minutes Features ===\n")
    
    features = [
        "MIN - Game minutes played",
        "avg_min - Season average minutes", 
        "min_vs_league - Minutes relative to league average",
        "min_recent_trend - Recent minutes trend vs season average",
        "min_usage_interaction - Minutes × Usage Rate interaction",
        "high_min_fatigue - High minutes followed by poor performance",
        "PTS_per_min, REB_per_min, etc. - Per-minute efficiency",
        "PTS_per_36, REB_per_36, etc. - Per-36 minute projections",
        "min_trend - Rolling minutes trend",
        "min_consistency - Minutes consistency (1/std dev)"
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"{i:2d}. {feature}")
    
    print(f"\nThese features help the model understand:")
    print(f"• Player workload and fatigue")
    print(f"• Efficiency per minute played")
    print(f"• Role changes (increased/decreased minutes)")
    print(f"• Matchup-specific minute adjustments")
    print(f"• Rest vs heavy usage impacts")

if __name__ == "__main__":
    test_minutes_impact()
    show_minutes_features()
    
    print("\n=== Summary ===")
    print("Minutes per game is now integrated into the predictive model through:")
    print("- Direct minutes features (current game, season average)")  
    print("- Efficiency metrics (stats per minute, per 36 minutes)")
    print("- Trend analysis (increasing/decreasing minutes)")
    print("- Interaction effects (minutes × usage rate)")
    print("- Fatigue indicators (high minutes impact on performance)")
    print("- League comparison (minutes vs NBA average)")
