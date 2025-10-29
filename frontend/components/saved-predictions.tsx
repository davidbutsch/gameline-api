"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { TrendingUp, TrendingDown, Trash2, Calendar, Target } from "lucide-react"

interface SavedPrediction {
  id: string
  player_name: string
  headshot_url: string
  bet_on: string
  confidence: number
  predicted_value: number
  category: string
  opponent: string
  betting_line: number
  timestamp: string
  result?: any
}

interface SavedPredictionsProps {
  predictions: SavedPrediction[]
  onRemovePrediction: (id: string) => void
}

export function SavedPredictions({ predictions, onRemovePrediction }: SavedPredictionsProps) {
  if (predictions.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
          <Target className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">No Saved Predictions</h3>
        <p className="text-sm text-muted-foreground">
          Save your predictions to track them here
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-foreground">Saved Predictions</h2>
        <Badge variant="outline" className="text-sm">
          {predictions.length} saved
        </Badge>
      </div>
      
      <div className="grid gap-4">
        {predictions.map((prediction) => (
          <Card key={prediction.id} className="border border-border hover:border-accent-primary/50 transition-colors">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Avatar className="w-12 h-12 border-2 border-border">
                    <AvatarImage 
                      src={prediction.headshot_url} 
                      alt={prediction.player_name}
                      className="object-cover"
                    />
                    <AvatarFallback className="bg-muted">
                      <Target className="w-6 h-6 text-muted-foreground" />
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle className="text-base">{prediction.player_name}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {prediction.category} vs {prediction.opponent}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemovePrediction(prediction.id)}
                  className="text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    {prediction.bet_on === "over" ? (
                      <TrendingUp className="w-4 h-4 text-accent-primary" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-accent-secondary" />
                    )}
                    <span className="text-sm font-medium text-foreground">Recommendation</span>
                  </div>
                  <Badge
                    variant="outline"
                    className={`text-sm font-bold ${
                      prediction.bet_on === "over"
                        ? "bg-accent-primary/20 text-accent-primary border-accent-primary"
                        : "bg-accent-secondary/20 text-accent-secondary border-accent-secondary"
                    }`}
                  >
                    {prediction.bet_on.toUpperCase()}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium text-foreground">Predicted Value</span>
                  </div>
                  <p className="text-lg font-bold text-foreground">
                    {prediction.predicted_value.toFixed(1)}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>{new Date(prediction.timestamp).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span>Confidence:</span>
                  <span className="font-medium text-foreground">
                    {prediction.confidence.toFixed(1)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
