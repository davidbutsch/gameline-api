"use client"

import { TrendingUp, TrendingDown, Activity, BarChart3, User, AlertCircle, Bookmark, BookmarkCheck, Target, Minus } from "lucide-react"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { LoadingAnimation } from "./loading-animation"

interface PredictionResultsProps {
  result: any
  player: any
  isLoading: boolean
  onSavePrediction?: (prediction: any) => void
  isSaved?: boolean
}

export function PredictionResults({ result, player, isLoading, onSavePrediction, isSaved }: PredictionResultsProps) {
  if (isLoading) {
    return <LoadingAnimation message="Analyzing Player Data..." />
  }

  // Debug logging to see what data we're receiving
  console.log("Prediction result data:", result)
  console.log("Opponent impact:", result.opponent_impact)
  console.log("Injury impact:", result.injury_impact)

  const isOver = result.bet_on === "over"
  const confidence = result.confidence || 0

  return (
    <div className="h-full overflow-y-auto space-y-6 animate-in fade-in-0 slide-in-from-bottom-4 duration-500 pr-2">
      {/* Main Prediction Card */}
      <Card className="border-2 border-accent-primary/20 shadow-xl">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16 border-2 border-accent-primary">
              <AvatarImage 
                src={result.headshot_url || player.headshot_url} 
                alt={result.player_name}
                className="object-cover"
              />
              <AvatarFallback className="bg-muted">
                <User className="w-8 h-8 text-muted-foreground" />
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <CardTitle className="text-xl text-foreground">{result.player_name}</CardTitle>
              <p className="text-sm text-muted-foreground">AI Prediction Analysis</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Main Prediction Display */}
          <div className="p-8 bg-gradient-to-br from-accent-primary/10 to-accent-secondary/10 rounded-xl border border-accent-primary/20 relative overflow-hidden">
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-5">
              <div className="absolute top-0 right-0 w-32 h-32 bg-accent-primary rounded-full -translate-y-16 translate-x-16"></div>
              <div className="absolute bottom-0 left-0 w-24 h-24 bg-accent-secondary rounded-full translate-y-12 -translate-x-12"></div>
            </div>
            
            <div className="relative text-center space-y-6">
              {/* Prediction Value with Visual Impact */}
              <div className="space-y-4">
                <div className="flex items-center justify-center gap-4 mb-4">
                  <div className={`p-4 rounded-full ${isOver ? 'bg-accent-primary/20' : 'bg-accent-secondary/20'}`}>
                {isOver ? (
                      <TrendingUp className="w-10 h-10 text-accent-primary" />
                    ) : (
                      <TrendingDown className="w-10 h-10 text-accent-secondary" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Predicted Value</p>
                    <span className="text-5xl font-bold text-foreground">
                      {result.predicted_value !== null && result.predicted_value !== undefined
                        ? result.predicted_value.toFixed(1)
                        : "N/A"}
                    </span>
                  </div>
              </div>
                
              <Badge
                variant="outline"
                  className={`text-2xl font-bold px-8 py-3 ${
                  isOver
                      ? "bg-accent-primary/20 text-accent-primary border-accent-primary shadow-lg"
                      : "bg-accent-secondary/20 text-accent-secondary border-accent-secondary shadow-lg"
                }`}
              >
                {result.bet_on.toUpperCase()}
              </Badge>
            </div>
              
              {/* Enhanced Confidence Meter */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground font-medium">AI Confidence</span>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-foreground">{confidence.toFixed(1)}%</span>
                    <div className={`w-3 h-3 rounded-full ${
                      confidence > 70 ? 'bg-green-500' : 
                      confidence > 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}></div>
                  </div>
              </div>
                
                <div className="relative">
                  <div className="h-6 bg-muted/50 rounded-full overflow-hidden border border-border/50">
                    <div
                      className="h-full bg-gradient-to-r from-accent-primary via-accent-secondary to-accent-primary rounded-full transition-all duration-1500 relative"
                    style={{ width: `${confidence}%` }}
                    >
                      <div className="absolute inset-0 bg-white/20 rounded-full"></div>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-2">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                  </div>
                </div>
              </div>
            </div>
          </div>


        </CardContent>
      </Card>

      {/* Player Averages Chart */}
      {result.player_averages && result.player_averages.season_averages && result.player_averages.recent_averages && (
        <Card className="border border-border shadow-lg overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-accent-primary/5 to-accent-secondary/5 p-6 m-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-accent-primary/10 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-accent-primary" />
              </div>
              <div>
                <CardTitle className="text-lg font-semibold text-foreground">Player Averages for {result.category || 'Points'}</CardTitle>
                <p className="text-sm text-muted-foreground">Historical performance comparison</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6 pt-0">
            {(() => {
              // Determine which category to show based on the result
              const category = result.category || 'Points'
              
              // Get the stat key based on category
              const getStatKey = (cat: string) => {
                const mapping: { [key: string]: string } = {
                  'Points': 'PTS',
                  'Rebounds': 'REB',
                  'Assists': 'AST',
                  'Blocks': 'BLK',
                  'Steals': 'STL',
                  'Points+Rebounds+Assists': 'POINTS+REBOUNDS+ASSISTS',
                  'Rebounds+Assists': 'REBOUNDS+ASSISTS',
                  'Points+Rebounds': 'POINTS+REBOUNDS',
                  'Points+Assists': 'POINTS+ASSISTS',
                  'Blocks+Steals': 'BLOCKS+STEALS'
                }
                return mapping[cat] || 'PTS'
              }
              
              const statKey = getStatKey(category)
              const seasonAvg = result.player_averages.season_averages[statKey] || 0
              const recentAvg = result.player_averages.recent_averages[statKey] || 0
              
              // Handle H2H averages - calculate combination stats if not available
              let h2hAvg = result.player_averages.h2h_averages?.[statKey] || 0
              if (h2hAvg === 0 && result.player_averages.h2h_averages) {
                const h2hData = result.player_averages.h2h_averages
                switch (statKey) {
                  case 'POINTS+REBOUNDS+ASSISTS':
                    h2hAvg = (h2hData.PTS || 0) + (h2hData.REB || 0) + (h2hData.AST || 0)
                    break
                  case 'REBOUNDS+ASSISTS':
                    h2hAvg = (h2hData.REB || 0) + (h2hData.AST || 0)
                    break
                  case 'POINTS+REBOUNDS':
                    h2hAvg = (h2hData.PTS || 0) + (h2hData.REB || 0)
                    break
                  case 'POINTS+ASSISTS':
                    h2hAvg = (h2hData.PTS || 0) + (h2hData.AST || 0)
                    break
                  case 'BLOCKS+STEALS':
                    h2hAvg = (h2hData.BLK || 0) + (h2hData.STL || 0)
                    break
                }
              }
              
              const bettingLine = result.betting_line || 0
              const maxValue = Math.max(seasonAvg, recentAvg, h2hAvg, bettingLine, 1) * 1.15 // Add 15% padding
              const chartHeight = 280
              const barSpacing = 16
              
              return (
                <div className="bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl p-6 border border-border/50">
                  {/* Chart Container with Y-axis and Plotting Area */}
                  <div className="flex relative" style={{ height: `${chartHeight}px` }}>
                    {/* Y-axis labels */}
                    <div className="flex flex-col justify-between text-xs text-muted-foreground pr-3 w-10 h-full">
                      {Array.from({length: 7}).map((_, i) => (
                        <div key={i} className="text-right font-medium">
                          {Math.round((maxValue / 6) * (6 - i))}
                        </div>
                      ))}
                    </div>
                    
                    {/* Plotting area with grid, bars, and betting line */}
                    <div className="flex-1 relative">
                      {/* Grid lines */}
                      <div className="absolute inset-0">
                        {Array.from({length: 6}).map((_, i) => (
                          <div 
                            key={i} 
                            className="absolute left-0 right-0 border-t border-border/20"
                            style={{ top: `${(i * chartHeight) / 5}px` }}
                          ></div>
                        ))}
                      </div>
                      
                      {/* Bars */}
                      <div className="absolute inset-0 flex items-end justify-around px-2">
                        {/* Season Average - Green */}
                        <div className="flex flex-col items-center" style={{ width: '30%' }}>
                          <div className="w-full">
                            <div 
                              className="w-full bg-green-500 rounded-t border-b-2 border-green-600 flex items-center justify-center"
                              style={{ 
                                height: `${(seasonAvg / maxValue) * chartHeight}px`,
                                minHeight: '12px'
                              }}
                            >
                              <span className="text-xs font-bold text-white">{seasonAvg.toFixed(1)}</span>
                            </div>
                          </div>
                        </div>
                        
                        {/* Recent Average - Orange */}
                        <div className="flex flex-col items-center" style={{ width: '30%' }}>
                          <div className="w-full">
                            <div 
                              className="w-full bg-orange-500 rounded-t border-b-2 border-orange-600 flex items-center justify-center"
                              style={{ 
                                height: `${(recentAvg / maxValue) * chartHeight}px`,
                                minHeight: '12px'
                              }}
                            >
                              <span className="text-xs font-bold text-white">{recentAvg.toFixed(1)}</span>
                            </div>
                          </div>
                        </div>
                        
                        {/* H2H Average - Dark Grey */}
                        {h2hAvg > 0 && (
                          <div className="flex flex-col items-center" style={{ width: '30%' }}>
                            <div className="w-full">
                              <div 
                                className="w-full bg-gray-600 rounded-t border-b-2 border-gray-700 flex items-center justify-center"
                                style={{ 
                                  height: `${(h2hAvg / maxValue) * chartHeight}px`,
                                  minHeight: '12px'
                                }}
                              >
                                <span className="text-xs font-bold text-white">{h2hAvg.toFixed(1)}</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* Betting Line - Horizontal dashed line */}
                      {bettingLine > 0 && (
                        <>
                          <div 
                            className="absolute left-0 right-0 border-t-2 border-dashed border-yellow-500 z-10"
                            style={{ 
                              bottom: `${(bettingLine / maxValue) * chartHeight}px`
                            }}
                          />
                          {/* Betting Line Label on the right */}
                          <div 
                            className="absolute bg-yellow-500 rounded px-2 py-0.5 whitespace-nowrap z-20"
                            style={{ 
                              bottom: `${(bettingLine / maxValue) * chartHeight - 10}px`,
                              right: '0px'
                            }}
                          >
                            <span className="text-xs font-bold text-white">Betting Line</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                  
                  {/* X-axis labels below the chart */}
                  <div className="flex justify-around mt-4 px-2">
                    <div className="w-[30%]">
                      <div className="text-sm font-medium text-muted-foreground text-center">Season</div>
                    </div>
                    <div className="w-[30%]">
                      <div className="text-sm font-medium text-muted-foreground text-center">Last 10 Games</div>
                    </div>
                    {h2hAvg > 0 && (
                      <div className="w-[30%]">
                        <div className="text-sm font-medium text-muted-foreground text-center">vs. {result.opponent_abbr || 'Opponent'}</div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })()}
          </CardContent>
        </Card>
      )}

      {/* Player Performance Chart */}
      {result.player_averages && (
        <Card className="border border-border shadow-lg overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-accent-primary/5 to-accent-secondary/5 p-6 m-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-accent-primary/10 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-accent-primary" />
              </div>
              <div>
                <CardTitle className="text-lg font-semibold text-foreground">Player Performance Trends</CardTitle>
                <p className="text-sm text-muted-foreground">Recent vs Season averages with trend analysis</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-6">
              {/* Key Stats Comparison */}
              {result.player_averages.recent_averages && result.player_averages.season_averages && (
                <div className="space-y-4">
                  <h4 className="text-lg font-semibold text-foreground">Key Statistics Comparison</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {['PTS', 'REB', 'AST', 'BLK', 'STL'].map((stat) => {
                      const recent = result.player_averages.recent_averages[stat]
                      const season = result.player_averages.season_averages[stat]
                      if (!recent || !season) return null
                      
                      const trend = recent > season ? 'up' : recent < season ? 'down' : 'neutral'
                      const percentage = season > 0 ? ((recent - season) / season * 100) : 0
                      const maxValue = Math.max(recent, season, 1)
                      
                      return (
                        <div key={stat} className="p-5 bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl border border-border/50 hover:border-accent-primary/30 transition-all duration-300">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className={`p-3 rounded-lg ${trend === 'up' ? 'bg-green-500/20' : trend === 'down' ? 'bg-red-500/20' : 'bg-muted/20'}`}>
                                {trend === 'up' ? (
                                  <TrendingUp className="w-5 h-5 text-green-500" />
                                ) : trend === 'down' ? (
                                  <TrendingDown className="w-5 h-5 text-red-500" />
                                ) : (
                                  <Minus className="w-5 h-5 text-muted-foreground" />
                                )}
                              </div>
                              <div className="min-w-0 flex-1">
                                <span className="text-lg font-bold text-foreground">{stat}</span>
                                <p className="text-xs text-muted-foreground">
                                  {stat === 'PTS' ? 'Per game' :
                                   stat === 'REB' ? 'Per game' :
                                   stat === 'AST' ? 'Per game' :
                                   stat === 'BLK' ? 'Per game' :
                                   stat === 'STL' ? 'Per game' : 'Per game'}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-2xl font-bold text-foreground">{recent.toFixed(1)}</p>
                              <p className="text-sm text-muted-foreground">Recent avg</p>
                            </div>
                          </div>
                          
                          <div className="space-y-3">
                            {/* Visual Comparison Bars */}
                            <div className="space-y-2">
                              <div className="flex justify-between text-xs text-muted-foreground">
                                <span>Recent Performance</span>
                                <span>{recent.toFixed(1)}</span>
                              </div>
                              <div className="relative">
                                <div className="h-4 bg-muted/50 rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-1000"
                                    style={{ width: `${(recent / maxValue) * 100}%` }}
                                  />
                                </div>
                              </div>
                              
                              <div className="flex justify-between text-xs text-muted-foreground">
                                <span>Season Average</span>
                                <span>{season.toFixed(1)}</span>
                              </div>
                              <div className="relative">
                                <div className="h-4 bg-muted/30 rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-gradient-to-r from-muted-foreground/50 to-muted-foreground/70 rounded-full transition-all duration-1000"
                                    style={{ width: `${(season / maxValue) * 100}%` }}
                                  />
                                </div>
                              </div>
                            </div>
                            
                            {/* Change Indicator */}
                            <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg mt-1">
                              <span className="text-sm font-medium text-foreground">Performance Change</span>
                              <div className="flex items-center gap-2">
                                <span className={`text-sm font-bold ${trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-muted-foreground'}`}>
                                  {percentage > 0 ? '+' : ''}{percentage.toFixed(1)}%
                                </span>
                                <div className={`w-2 h-2 rounded-full ${trend === 'up' ? 'bg-green-500' : trend === 'down' ? 'bg-red-500' : 'bg-muted-foreground'}`}></div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Head to Head Stats */}
      {result.h2h_list && result.h2h_list.length > 0 && (
        <Card className="border border-border shadow-lg overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-accent-secondary/5 to-accent-primary/5 p-6 m-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-accent-secondary/10 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-accent-secondary" />
              </div>
              <div>
                <CardTitle className="text-lg font-semibold text-foreground">Recent Head-to-Head Games</CardTitle>
                <p className="text-sm text-muted-foreground">Historical performance against this opponent</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-4">
              {result.h2h_list.slice(0, 5).map((game: any, i: number) => (
                <div key={i} className="p-5 bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl border border-border/50 hover:border-accent-secondary/30 transition-all duration-300 hover:shadow-md">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-3 bg-accent-secondary/20 rounded-lg">
                        <Activity className="w-5 h-5 text-accent-secondary" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">{game.Game_Date || "Recent Game"}</p>
                        <p className="text-sm text-muted-foreground">{game.Matchup || "vs Opponent"}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2">
                        <div className="p-2 bg-accent-primary/20 rounded-lg">
                          <Target className="w-4 h-4 text-accent-primary" />
                        </div>
                        <div>
                          <p className="text-3xl font-bold text-foreground">{game.PTS?.toFixed(1) || "N/A"}</p>
                          <p className="text-xs text-muted-foreground">Points</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-3">
                    <div className="text-center p-3 bg-background/60 rounded-lg border border-border/30 hover:border-accent-primary/30 transition-colors">
                      <div className="flex items-center justify-center mb-1">
                        <div className="w-2 h-2 bg-accent-primary rounded-full"></div>
                      </div>
                      <p className="text-xs text-muted-foreground font-medium">REB</p>
                      <p className="font-bold text-foreground text-lg">{game.REB?.toFixed(1) || "N/A"}</p>
                    </div>
                    <div className="text-center p-3 bg-background/60 rounded-lg border border-border/30 hover:border-accent-secondary/30 transition-colors">
                      <div className="flex items-center justify-center mb-1">
                        <div className="w-2 h-2 bg-accent-secondary rounded-full"></div>
                      </div>
                      <p className="text-xs text-muted-foreground font-medium">AST</p>
                      <p className="font-bold text-foreground text-lg">{game.AST?.toFixed(1) || "N/A"}</p>
                    </div>
                    <div className="text-center p-3 bg-background/60 rounded-lg border border-border/30 hover:border-green-500/30 transition-colors">
                      <div className="flex items-center justify-center mb-1">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      </div>
                      <p className="text-xs text-muted-foreground font-medium">BLK</p>
                      <p className="font-bold text-foreground text-lg">{game.BLK?.toFixed(1) || "N/A"}</p>
                    </div>
                    <div className="text-center p-3 bg-background/60 rounded-lg border border-border/30 hover:border-blue-500/30 transition-colors">
                      <div className="flex items-center justify-center mb-1">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      </div>
                      <p className="text-xs text-muted-foreground font-medium">STL</p>
                      <p className="font-bold text-foreground text-lg">{game.STL?.toFixed(1) || "N/A"}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Opponent Team Analysis */}
      {result.opp_averages && (
        <Card className="border border-border shadow-lg overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-accent-primary/5 to-accent-secondary/5 p-6 m-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-accent-primary/10 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-accent-primary" />
              </div>
              <div>
                <CardTitle className="text-lg font-semibold text-foreground">Opponent Team Analysis</CardTitle>
                <p className="text-sm text-muted-foreground">How the opposing team performs defensively</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(result.opp_averages)
                .filter(([key]) => ['PTS', 'REB', 'AST', 'BLK', 'STL', 'PACE'].includes(key))
                .map(([key, value]) => {
                const numValue = typeof value === "number" ? value : 0
                
                // Set appropriate max values for different stats
                const getMaxValue = (stat: string) => {
                  switch(stat) {
                    case 'PTS': return 120
                    case 'REB': return 50
                    case 'AST': return 30
                    case 'BLK': return 10
                    case 'STL': return 15
                    case 'PACE': return 110
                    default: return 50
                  }
                }
                
                const maxValue = getMaxValue(key)
                const percentage = Math.min((numValue / maxValue) * 100, 100)
                const intensity = percentage > 70 ? 'high' : percentage > 40 ? 'medium' : 'low'
                
                return (
                  <div key={key} className="p-5 bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl border border-border/50 hover:border-accent-primary/30 transition-all duration-300 hover:shadow-md">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <div className={`p-2 rounded-lg ${
                          intensity === 'high' ? 'bg-red-500/20' : 
                          intensity === 'medium' ? 'bg-yellow-500/20' : 'bg-green-500/20'
                        }`}>
                          <Target className={`w-4 h-4 ${
                            intensity === 'high' ? 'text-red-500' : 
                            intensity === 'medium' ? 'text-yellow-500' : 'text-green-500'
                          }`} />
                        </div>
                        <div>
                          <p className="text-xs font-medium text-foreground capitalize">{key}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-base font-bold text-foreground">
                          {numValue.toFixed(1)}
                        </p>
                        <p className={`text-xs font-medium ${
                          intensity === 'high' ? 'text-red-500' : 
                          intensity === 'medium' ? 'text-yellow-500' : 'text-green-500'
                        }`}>
                          {intensity.toUpperCase()}
                        </p>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Team Average</span>
                        <span>{percentage.toFixed(0)}%</span>
                      </div>
                      <div className="relative">
                        <div className="h-4 bg-muted/50 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all duration-1000 ${
                              intensity === 'high' ? 'bg-gradient-to-r from-red-500 to-red-600' :
                              intensity === 'medium' ? 'bg-gradient-to-r from-yellow-500 to-yellow-600' :
                              'bg-gradient-to-r from-green-500 to-green-600'
                            }`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Low</span>
                        <span>High</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Opponent Impact Analysis - Extract from existing data */}
      {result.opp_averages && (
        <Card className="border border-border shadow-lg overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-accent-primary/5 to-accent-secondary/5 p-6 m-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-accent-primary/10 rounded-lg flex items-center justify-center">
                <Target className="w-5 h-5 text-accent-primary" />
              </div>
              <div>
                <CardTitle className="text-lg font-semibold text-foreground">Opponent Impact Analysis</CardTitle>
                <p className="text-sm text-muted-foreground">How the opponent affects this prediction</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl border border-border/50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-accent-primary/20 rounded-lg">
                      <Target className="w-4 h-4 text-accent-primary" />
                    </div>
                    <span className="text-sm font-semibold text-foreground">Opponent Impact Factor</span>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-foreground">
                      {(() => {
                        // Look for "Impact Factor" in the message
                        const message = result.message || ""
                        const impactMatch = message.match(/Impact Factor:\s*([+-]?\d+\.?\d*%?)/i)
                        return impactMatch ? impactMatch[1] : "N/A"
                      })()}
                    </p>
                    <p className="text-xs text-muted-foreground">Impact Factor</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Opponent Influence</span>
                    <span>{(() => {
                      const message = result.message || ""
                      const impactMatch = message.match(/Impact Factor:\s*([+-]?\d+\.?\d*%?)/i)
                      return impactMatch ? impactMatch[1] : "0%"
                    })()}</span>
                  </div>
                  <div className="relative">
                    <div className="h-3 bg-muted/50 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary rounded-full transition-all duration-1000"
                        style={{ width: `${(() => {
                          const message = result.message || ""
                          const impactMatch = message.match(/Impact Factor:\s*([+-]?\d+\.?\d*%?)/i)
                          if (impactMatch) {
                            const value = parseFloat(impactMatch[1].replace('%', ''))
                            return Math.min(Math.abs(value), 100)
                          }
                          return 0
                        })()}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl border border-border/50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-accent-secondary/20 rounded-lg">
                      <Activity className="w-4 h-4 text-accent-secondary" />
                    </div>
                    <span className="text-sm font-semibold text-foreground">Matchup Analysis</span>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-foreground">
                      {(() => {
                        // Use pace to determine matchup difficulty
                        const pace = result.opp_averages.PACE || 100
                        return pace > 105 ? "Fast" : pace < 95 ? "Slow" : "Neutral"
                      })()}
                    </p>
                    <p className="text-xs text-muted-foreground">Pace</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Team Pace</span>
                    <span>{result.opp_averages.PACE ? `${result.opp_averages.PACE.toFixed(1)}` : "N/A"}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {(() => {
                      const pace = result.opp_averages.PACE || 100
                      return pace > 105 ? "High-tempo opponent" : 
                             pace < 95 ? "Low-tempo opponent" : 
                             "Average pace opponent"
                    })()}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Injury Impact Analysis with Team Injuries */}
      {result.message && result.message.includes("Injury Impact Analysis") && (
        <Card className="border border-border shadow-lg overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-accent-secondary/5 to-accent-primary/5 p-6 m-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-accent-secondary/10 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-accent-secondary" />
              </div>
              <div>
                <CardTitle className="text-lg font-semibold text-foreground">Injury Impact Analysis</CardTitle>
                <p className="text-sm text-muted-foreground">How injuries affect this prediction</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-6">
              {/* Net Injury Effect - Full Width at Top */}
              <div className="p-6 bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl border border-border/50">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg flex-shrink-0 ${
                    (() => {
                      const message = result.message || ""
                      const netEffectMatch = message.match(/Net Injury Effect:\s*(.+)/i)
                      const netEffect = netEffectMatch ? netEffectMatch[1].trim() : "Neutral"
                      return netEffect.toLowerCase().includes('positive') ? 'bg-green-500/20' :
                             netEffect.toLowerCase().includes('negative') ? 'bg-red-500/20' : 'bg-muted/20'
                    })()
                  }`}>
                    <Activity className={`w-5 h-5 ${
                      (() => {
                        const message = result.message || ""
                        const netEffectMatch = message.match(/Net Injury Effect:\s*(.+)/i)
                        const netEffect = netEffectMatch ? netEffectMatch[1].trim() : "Neutral"
                        return netEffect.toLowerCase().includes('positive') ? 'text-green-500' :
                               netEffect.toLowerCase().includes('negative') ? 'text-red-500' : 'text-muted-foreground'
                      })()
                    }`} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-muted-foreground mb-1">Net Injury Effect</p>
                    <p className="text-xl font-bold text-foreground">
                      {(() => {
                        const message = result.message || ""
                        const netEffectMatch = message.match(/Net Injury Effect:\s*(.+)/i)
                        return netEffectMatch ? netEffectMatch[1].trim() : "Neutral"
                      })()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Team Injuries - Side by Side */}
              {(result.team_injuries && result.team_injuries.length > 0) || (result.opponent_injuries && result.opponent_injuries.length > 0) ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {result.team_injuries && result.team_injuries.length > 0 && (
                    <div className="p-4 bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl border border-border/50">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="p-1.5 bg-accent-primary/20 rounded">
                          <Activity className="w-3.5 h-3.5 text-accent-primary" />
                        </div>
                        <h4 className="text-sm font-semibold text-foreground">Player's Team Injuries</h4>
                      </div>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {result.team_injuries.map((injury: any, i: number) => (
                          <div key={i} className="flex items-center justify-between text-xs py-1.5 px-2 bg-background/50 rounded border border-border/30">
                            <span className="text-foreground font-medium">{injury.player_name}</span>
                            <span className={`font-semibold ${injury.status === 'Out' ? 'text-red-400' : injury.status === 'Questionable' ? 'text-yellow-400' : 'text-orange-400'}`}>
                              {injury.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {result.opponent_injuries && result.opponent_injuries.length > 0 && (
                    <div className="p-4 bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl border border-border/50">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="p-1.5 bg-accent-secondary/20 rounded">
                          <Target className="w-3.5 h-3.5 text-accent-secondary" />
                        </div>
                        <h4 className="text-sm font-semibold text-foreground">Opponent Injuries ({result.opponent_abbr})</h4>
                      </div>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {result.opponent_injuries.map((injury: any, i: number) => (
                          <div key={i} className="flex items-center justify-between text-xs py-1.5 px-2 bg-background/50 rounded border border-border/30">
                            <span className="text-foreground font-medium">{injury.player_name}</span>
                            <span className={`font-semibold ${injury.status === 'Out' ? 'text-red-400' : injury.status === 'Questionable' ? 'text-yellow-400' : 'text-orange-400'}`}>
                              {injury.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-6 bg-gradient-to-br from-muted/20 to-muted/40 rounded-xl border border-border/50 flex flex-col items-center justify-center gap-2">
                  <div className="p-2 bg-green-500/20 rounded">
                    <Activity className="w-5 h-5 text-green-500" />
                  </div>
                  <p className="text-sm font-medium text-foreground">No Active Injuries</p>
                  <p className="text-xs text-muted-foreground text-center">Both teams are healthy</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Save Prediction Button */}
      {onSavePrediction && (
        <div className="flex justify-center">
          <button
            onClick={() => onSavePrediction(result)}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
              isSaved 
                ? 'bg-green-500 hover:bg-green-600 text-white' 
                : 'bg-accent-primary hover:bg-accent-primary/90 text-white'
            }`}
          >
            {isSaved ? (
              <>
                <BookmarkCheck className="w-5 h-5" />
                Prediction Saved
              </>
            ) : (
              <>
                <Bookmark className="w-5 h-5" />
                Save Prediction
              </>
            )}
          </button>
        </div>
      )}

      {/* Disclaimer */}
      <div className="p-4 bg-muted/30 border border-border rounded-lg">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
          <p className="text-xs text-muted-foreground leading-relaxed">
            This prediction is generated by AI and should be used for informational purposes only. Past performance does
            not guarantee future results. Please gamble responsibly.
          </p>
        </div>
      </div>
    </div>
  )
}
