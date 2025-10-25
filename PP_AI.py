from predictive_model import AdvancedNBAPlayerPredictor
import bet_calculations as bc


def get_category_choice(choice):
    categories = {
        '1': 'Points',
        '2': 'Rebounds', 
        '3': 'Assists',
        '4': 'Blocks',
        '5': 'Steals',
        '6': 'Points+Rebounds+Assists',
        '7': 'Rebounds+Assists',
        '8': 'Points+Rebounds',
        '9': 'Points+Assists',
        '10': 'Blocks+Steals'
    }
    return categories.get(choice, 'Points')

def main():
    try:
        print("=== NBA Betting Predictor ===")
        print()
        
        player_name = input("Name of NBA Player: ").strip()
        if not player_name:
            print("Error: Player name cannot be empty")
            return
            
        print("\nWhat category is the bet:")
        print("1) Points\n2) Rebounds\n3) Assists\n4) Blocks\n5) Steals")
        print("6) Points+Rebounds+Assists\n7) Rebounds+Assists\n8) Points+Rebounds")
        print("9) Points+Assists\n10) Blocks+Steals")
        category_choice = input("Enter choice (1-10): ").strip()
        category = get_category_choice(category_choice)
        
        opponent_abbr = input("Enter the abbreviation of the opposing team (e.g., BOS): ").strip().upper()
        if not opponent_abbr:
            print("Error: Team abbreviation cannot be empty")
            return
            
        print("\n1) Regular Season\n2) Playoffs")
        season_type_choice = input("Enter choice (1-2): ").strip()
        season_type = 'Playoffs' if season_type_choice == '2' else 'Regular Season'
        
        try:
            betting_line = float(input("Enter the betting line: "))
        except ValueError:
            print("Error: Betting line must be a number")
            return

        print(f"\nFetching data for {player_name}...")
        
        # Get player ID
        player_info = bc.get_player_id(player_name)
        if not player_info:
            print(f"Error: Player '{player_name}' not found")
            return
            
        player_id = player_info['player_id']
        print(f"Found player: {player_name} (ID: {player_id})")
        
        # Verify team exists
        team_id = bc.get_team_id(opponent_abbr)
        if not team_id:
            print(f"Error: Team '{opponent_abbr}' not found")
            return
            
        print(f"Found opponent team: {opponent_abbr} (ID: {team_id})")
        
        print(f"\nGenerating prediction for {player_name} vs {opponent_abbr}...")
        print(f"Category: {category}")
        print(f"Betting Line: {betting_line}")
        print(f"Season Type: {season_type}")
        print()
        
        # Initialize predictor
        predictor = AdvancedNBAPlayerPredictor()
        
        # Make prediction
        result = predictor.predict_over_under(
            player_id=player_id,
            category=category,
            opponent_abbr=opponent_abbr,
            season_type=season_type,
            betting_line=betting_line
        )

        print("=" * 60)
        print("PREDICTION RESULTS")
        print("=" * 60)
        print(f"Player: {player_name}")
        print(f"Category: {category}")
        print(f"Opponent: {opponent_abbr}")
        print(f"Betting Line: {betting_line}")
        print()
        print(f"Predicted Value: {result['predicted_value']}")
        print(f"Confidence Interval: {result['confidence_interval']}")
        print(f"Bet Recommendation: {result['bet_on'].upper()}")
        print(f"Confidence: {result['confidence']:.1f}%")
        print()
        print("DETAILED ANALYSIS:")
        print("-" * 40)
        print(result['message'])

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
