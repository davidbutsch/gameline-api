"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2, Zap } from "lucide-react"
import { fetchTeams, makePrediction, type Team } from "@/lib/api"

interface PredictionFormProps {
  player: any
  onPredictionComplete: (result: any) => void
  onLoadingChange: (loading: boolean) => void
}

const CATEGORIES = [
  { value: "Points", label: "Points" },
  { value: "Rebounds", label: "Rebounds" },
  { value: "Assists", label: "Assists" },
  { value: "Blocks", label: "Blocks" },
  { value: "Steals", label: "Steals" },
  { value: "Points+Rebounds+Assists", label: "Points + Rebounds + Assists" },
  { value: "Rebounds+Assists", label: "Rebounds + Assists" },
  { value: "Points+Rebounds", label: "Points + Rebounds" },
  { value: "Points+Assists", label: "Points + Assists" },
  { value: "Blocks+Steals", label: "Blocks + Steals" },
]

const SEASON_TYPES = [
  { value: "Regular Season", label: "Regular Season" },
  { value: "Playoffs", label: "Playoffs" },
]

export function PredictionForm({ player, onPredictionComplete, onLoadingChange }: PredictionFormProps) {
  const [teams, setTeams] = useState<Team[]>([])
  const [category, setCategory] = useState("Points")
  const [opponentAbbr, setOpponentAbbr] = useState("")
  const [bettingLine, setBettingLine] = useState("")
  const [seasonType, setSeasonType] = useState("Regular Season")
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const bettingLineRef = useRef<HTMLInputElement>(null)


  useEffect(() => {
    const loadTeams = async () => {
      try {
        const data = await fetchTeams()
        setTeams(data)
      } catch (error) {
        console.error("Error fetching teams:", error)
      }
    }

    loadTeams()
  }, [])

  // Auto-focus betting line when player is selected
  useEffect(() => {
    if (player?.full_name && bettingLineRef.current) {
      bettingLineRef.current.focus()
    }
  }, [player])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!bettingLine || !opponentAbbr || !player?.full_name) {
      console.error("Missing required data:", { bettingLine, opponentAbbr, player: player?.full_name })
      return
    }

    setIsSubmitting(true)
    setIsLoading(true)
    onLoadingChange(true)

    try {
      const result = await makePrediction({
        player_name: player.full_name,
        category,
        opponent_abbr: opponentAbbr,
        betting_line: Number.parseFloat(bettingLine),
        season_type: seasonType,
      })
      onPredictionComplete(result)
    } catch (error) {
      console.error("Error making prediction:", error)
    } finally {
      setIsSubmitting(false)
      setIsLoading(false)
      onLoadingChange(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="category" className="text-sm font-medium text-foreground">
          Stat Category
        </Label>
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger id="category" className="h-11 bg-background border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CATEGORIES.map((cat) => (
              <SelectItem key={cat.value} value={cat.value}>
                {cat.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="opponent" className="text-sm font-medium text-foreground">
          Opponent Team
        </Label>
        <Select value={opponentAbbr} onValueChange={setOpponentAbbr}>
          <SelectTrigger id="opponent" className="h-11 bg-background border-border">
            <SelectValue placeholder="Select opponent..." />
          </SelectTrigger>
          <SelectContent>
            {teams.map((team) => (
              <SelectItem key={team.id} value={team.abbreviation}>
                {team.abbreviation} - {team.full_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="betting-line" className="text-sm font-medium text-foreground">
          Betting Line
        </Label>
        <Input
          ref={bettingLineRef}
          id="betting-line"
          type="number"
          step="0.5"
          placeholder="e.g., 25.5"
          value={bettingLine}
          onChange={(e) => setBettingLine(e.target.value)}
          className="h-11 bg-background border-border"
          required
        />
        <p className="text-xs text-muted-foreground">
          Enter the betting line from your sportsbook
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="season-type" className="text-sm font-medium text-foreground">
          Season Type
        </Label>
        <Select value={seasonType} onValueChange={setSeasonType}>
          <SelectTrigger id="season-type" className="h-11 bg-background border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SEASON_TYPES.map((type) => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>


      <Button
        type="submit"
        className="w-full h-12 bg-accent-primary hover:bg-accent-primary/90 text-white font-semibold transition-all duration-200"
        disabled={isSubmitting || !bettingLine || !opponentAbbr || !player?.full_name}
      >
        {isSubmitting ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            Analyzing Player Data...
          </>
        ) : (
          <>
            <Zap className="w-5 h-5 mr-2" />
            Generate Prediction
          </>
        )}
      </Button>
    </form>
  )
}
