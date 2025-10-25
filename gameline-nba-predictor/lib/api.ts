// API configuration and helper functions for GameLine backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001"

export interface Player {
  id: number
  full_name: string
  first_name: string
  last_name: string
  headshot_url?: string
  team_abbreviation?: string
  position?: string
}

export interface Team {
  id: number
  abbreviation: string
  full_name: string
}

export interface PredictionRequest {
  player_name: string
  category: string
  opponent_abbr: string
  betting_line: number
  season_type: string
}

export interface PredictionResponse {
  player_name: string
  bet_on: string
  confidence: number
  confidence_interval: string
  predicted_value: number
  headshot_url: string
  message: string
  h2h_list: Array<{
    AST: number
    BLK: number
    Game_Date: string
    Matchup: string
    PTS: number
    REB: number
    STL: number
  }>
  player_averages: {
    recent_averages: Record<string, number>
    season_averages: Record<string, number>
    season_long_averages: Record<string, number>
  }
  opp_averages: Record<string, number>
  opponent_impact?: {
    impact_factor: string
    impact_percentage: number
    matchup_type: string
    defensive_rating: number
    analysis: string
  }
  injury_impact?: {
    player_adjustment: number
    team_impact: number
    opponent_impact: number
    net_effect: string
  }
}

// Fetch all players
export async function fetchPlayers(): Promise<Player[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/all-players`)
    if (!response.ok) {
      throw new Error(`Failed to fetch players: ${response.statusText}`)
    }
    return await response.json()
  } catch (error) {
    console.error("Error fetching players:", error)
    throw error
  }
}

// Fetch all teams
export async function fetchTeams(): Promise<Team[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/teams`)
    if (!response.ok) {
      throw new Error(`Failed to fetch teams: ${response.statusText}`)
    }
    return await response.json()
  } catch (error) {
    console.error("Error fetching teams:", error)
    throw error
  }
}

// Fetch player details including headshot
export async function fetchPlayerDetails(playerName: string): Promise<Player> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/player-details/${encodeURIComponent(playerName)}`)
    if (!response.ok) {
      throw new Error(`Failed to fetch player details: ${response.statusText}`)
    }
    return await response.json()
  } catch (error) {
    console.error("Error fetching player details:", error)
    throw error
  }
}

// Make prediction
export async function makePrediction(request: PredictionRequest): Promise<PredictionResponse> {
  try {
    const params = new URLSearchParams({
      player_name: request.player_name,
      category: request.category,
      opponent_abbr: request.opponent_abbr,
      betting_line: request.betting_line.toString(),
      season_type: request.season_type,
    })

    const response = await fetch(`${API_BASE_URL}/api/predict?${params}`)
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || `Prediction failed: ${response.statusText}`)
    }
    return await response.json()
  } catch (error) {
    console.error("Error making prediction:", error)
    throw error
  }
}
