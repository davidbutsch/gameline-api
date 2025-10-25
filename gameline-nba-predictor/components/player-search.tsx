"use client"

import { useState, useEffect } from "react"
import { Search, Loader2, User } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { fetchPlayers, fetchPlayerDetails, type Player } from "@/lib/api"

interface PlayerSearchProps {
  onPlayerSelect: (player: Player) => void
  selectedPlayer: Player | null
}

export function PlayerSearch({ onPlayerSelect, selectedPlayer }: PlayerSearchProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [players, setPlayers] = useState<Player[]>([])
  const [filteredPlayers, setFilteredPlayers] = useState<Player[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)

  // Generate headshot URL for players
  const getPlayerHeadshot = (player: Player) => {
    if (player.headshot_url) return player.headshot_url
    // Use NBA's standard headshot URL format
    return `https://cdn.nba.com/headshots/nba/latest/1040x760/${player.id}.png`
  }

  // Add some basic team info for better display
  const getPlayerDisplayInfo = (player: Player) => {
    return {
      team: player.team_abbreviation || "NBA",
      position: player.position || "Player"
    }
  }

  useEffect(() => {
    const loadPlayers = async () => {
      try {
        const data = await fetchPlayers()
        setPlayers(data)
        setIsLoading(false)
      } catch (error) {
        console.error("Error fetching players:", error)
        setIsLoading(false)
      }
    }

    loadPlayers()
  }, [])

  // Filter players based on search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredPlayers([])
      setSelectedIndex(-1)
      return
    }

    const query = searchQuery.toLowerCase()
    const filtered = players
      .filter(
        (player) =>
          player.full_name?.toLowerCase().includes(query) ||
          player.first_name?.toLowerCase().includes(query) ||
          player.last_name?.toLowerCase().includes(query),
      )
      .slice(0, 8) // Limit to 8 results

    setFilteredPlayers(filtered)
    setSelectedIndex(-1)
    setShowDropdown(true)
  }, [searchQuery, players])

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || filteredPlayers.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => (prev + 1) % filteredPlayers.length)
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => prev <= 0 ? filteredPlayers.length - 1 : prev - 1)
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < filteredPlayers.length) {
          handlePlayerSelect(filteredPlayers[selectedIndex])
        }
        break
      case 'Escape':
        setShowDropdown(false)
        setSelectedIndex(-1)
        break
    }
  }

  const handlePlayerSelect = async (player: Player) => {
    setSearchQuery(player.full_name)
    setShowDropdown(false)
    
    // Immediately select the player for instant feedback
    const immediatePlayer = {
      ...player,
      full_name: player.full_name || (player.first_name && player.last_name ? player.first_name + ' ' + player.last_name : 'Unknown Player')
    }
    onPlayerSelect(immediatePlayer)

    // Then fetch detailed info in the background and update
    try {
      const detailedPlayer = await fetchPlayerDetails(player.full_name)
      
      // Update with detailed info (only if different from immediate)
      const playerWithFullName = {
        ...detailedPlayer,
        full_name: detailedPlayer.full_name || player.full_name || 'Unknown Player'
      }
      
      // Only update if we got new data
      if (detailedPlayer.headshot_url || detailedPlayer.team_abbreviation) {
        onPlayerSelect(playerWithFullName)
      }
    } catch (error) {
      console.error("Error fetching player details:", error)
      // Keep the immediate selection if detailed fetch fails
    }
  }

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search for a player..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={() => searchQuery && setShowDropdown(true)}
          onKeyDown={handleKeyDown}
          className="pl-10 h-12 bg-background border-border"
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground animate-spin" />
        )}
      </div>

      {/* Dropdown */}
      {showDropdown && filteredPlayers.length > 0 && (
        <div className="absolute top-full mt-2 w-full bg-card border border-border rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
          {filteredPlayers.map((player, index) => (
            <button
              key={player.id}
              onClick={() => handlePlayerSelect(player)}
              className={`w-full flex items-center gap-3 p-3 transition-colors text-left border-b border-border last:border-b-0 ${
                index === selectedIndex 
                  ? 'bg-accent-primary/20 border-accent-primary/30' 
                  : 'hover:bg-accent/50'
              }`}
            >
              <Avatar className="w-12 h-12 border-2 border-border">
                <AvatarImage 
                  src={getPlayerHeadshot(player)} 
                  alt={player.full_name}
                  className="object-cover"
                />
                <AvatarFallback className="bg-muted">
                  <User className="w-6 h-6 text-muted-foreground" />
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-foreground truncate">{player.full_name}</p>
                <p className="text-sm text-muted-foreground">
                  {getPlayerDisplayInfo(player).team} • {getPlayerDisplayInfo(player).position}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Selected Player Display */}
      {selectedPlayer && !showDropdown && (
        <div className="mt-4 p-4 bg-accent/10 border border-accent-primary/20 rounded-lg">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16 border-2 border-accent-primary">
              <AvatarImage 
                src={getPlayerHeadshot(selectedPlayer)} 
                alt={selectedPlayer.full_name}
                className="object-cover"
              />
              <AvatarFallback className="bg-muted">
                <User className="w-8 h-8 text-muted-foreground" />
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="font-bold text-lg text-foreground">{selectedPlayer.full_name}</p>
              <p className="text-sm text-muted-foreground">
                {getPlayerDisplayInfo(selectedPlayer).team} • {getPlayerDisplayInfo(selectedPlayer).position}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
