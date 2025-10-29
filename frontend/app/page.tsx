"use client"

import { useState } from "react"
import { Search, TrendingUp, Activity, Target, CheckCircle, Bookmark } from "lucide-react"
import { PlayerSearch } from "@/components/player-search"
import { PredictionForm } from "@/components/prediction-form"
import { PredictionResults } from "@/components/prediction-results"
import { SavedPredictions } from "@/components/saved-predictions"
import { Logo } from "@/components/logo"
import { LoadingAnimation } from "@/components/loading-animation"

export default function HomePage() {
  const [selectedPlayer, setSelectedPlayer] = useState<any>(null)
  const [predictionResult, setPredictionResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [savedPredictions, setSavedPredictions] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState<'predict' | 'saved'>('predict')

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Logo size="md" />
              <div>
                <h1 className="text-2xl font-bold text-foreground">GameLine</h1>
                <p className="text-xs text-muted-foreground">AI-Powered NBA Predictions</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-6 text-sm">
                <button
                  onClick={() => setActiveTab('predict')}
                  className={`transition-colors ${
                    activeTab === 'predict'
                      ? 'text-foreground font-medium'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Predict
                </button>
                <button
                  onClick={() => setActiveTab('saved')}
                  className={`flex items-center gap-1 transition-colors ${
                    activeTab === 'saved'
                      ? 'text-foreground font-medium'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Bookmark className="w-4 h-4" />
                  Saved ({savedPredictions.length})
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="border-b border-border bg-gradient-to-b from-card/30 to-background">
        <div className="container mx-auto px-4 py-12">
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent-primary/10 border border-accent-primary/20 text-accent-primary text-sm font-medium mb-4">
              <TrendingUp className="w-4 h-4" />
              Advanced ML Predictions
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-foreground text-balance">Make Smarter NBA Prop Bets</h2>
            <p className="text-lg text-muted-foreground text-balance max-w-2xl mx-auto">
              Get AI-powered predictions for player performance with confidence intervals, head-to-head analysis, and
              real-time injury data.
            </p>
          </div>
        </div>
      </section>

      {/* Success Notification */}
      {showSuccess && (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-right-4 duration-300">
          <div className="bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">Prediction Generated Successfully!</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <section className="container mx-auto px-4 py-12">
        <div className="max-w-7xl mx-auto">
          {activeTab === 'predict' ? (
            <div className="space-y-8">
              {/* Progress Steps */}
              <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-8">
                    {/* Step 1: Player Selection */}
                    <div className={`flex items-center space-x-3 ${selectedPlayer ? 'text-accent-primary' : 'text-muted-foreground'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        selectedPlayer ? 'bg-accent-primary text-white' : 'bg-muted'
                      }`}>
                        {selectedPlayer ? <CheckCircle className="w-5 h-5" /> : '1'}
                      </div>
                      <div>
                        <p className="font-medium">Select Player</p>
                        <p className="text-sm text-muted-foreground">Choose your NBA player</p>
                      </div>
                    </div>

                    {/* Step 2: Configure Bet */}
                    <div className={`flex items-center space-x-3 ${selectedPlayer && !predictionResult ? 'text-accent-primary' : 'text-muted-foreground'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        selectedPlayer ? 'bg-accent-primary text-white' : 'bg-muted'
                      }`}>
                        {selectedPlayer ? (predictionResult ? <CheckCircle className="w-5 h-5" /> : '2') : '2'}
                      </div>
                      <div>
                        <p className="font-medium">Configure Bet</p>
                        <p className="text-sm text-muted-foreground">Set your parameters</p>
                      </div>
                    </div>

                    {/* Step 3: Get Prediction */}
                    <div className={`flex items-center space-x-3 ${predictionResult ? 'text-accent-primary' : 'text-muted-foreground'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        predictionResult ? 'bg-accent-primary text-white' : 'bg-muted'
                      }`}>
                        {predictionResult ? <CheckCircle className="w-5 h-5" /> : '3'}
                      </div>
                      <div>
                        <p className="font-medium">AI Prediction</p>
                        <p className="text-sm text-muted-foreground">Get your analysis</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid lg:grid-cols-2 gap-8">
                {/* Left Column - Interactive Steps */}
                <div className="space-y-6">
                  {/* Step 1: Player Search */}
                  <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="w-10 h-10 bg-accent-primary/10 rounded-lg flex items-center justify-center">
                        <Search className="w-5 h-5 text-accent-primary" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-foreground">Step 1: Choose Your Player</h3>
                        <p className="text-sm text-muted-foreground">Search and select any active NBA player</p>
                      </div>
                    </div>
                    <PlayerSearch 
                      onPlayerSelect={setSelectedPlayer} 
                      selectedPlayer={selectedPlayer} 
                    />
                  </div>

                  {/* Step 2: Prediction Form */}
                  {selectedPlayer && (
                    <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 bg-accent-secondary/10 rounded-lg flex items-center justify-center">
                          <Target className="w-5 h-5 text-accent-secondary" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-foreground">Step 2: Configure Your Bet</h3>
                          <p className="text-sm text-muted-foreground">Set the betting line and parameters</p>
                        </div>
                      </div>
                      <PredictionForm
                        player={selectedPlayer}
                        onPredictionComplete={(result) => {
                          setPredictionResult(result)
                          setIsLoading(false)
                          setShowSuccess(true)
                          setTimeout(() => setShowSuccess(false), 3000)
                        }}
                        onLoadingChange={setIsLoading}
                      />
                    </div>
                  )}
                </div>

                {/* Right Column - Results */}
                <div className="lg:sticky lg:top-24 h-[calc(100vh-8rem)] lg:h-[calc(100vh-12rem)]">
                  {predictionResult ? (
                    <PredictionResults 
                      result={predictionResult} 
                      player={selectedPlayer} 
                      isLoading={isLoading}
                      onSavePrediction={(prediction) => {
                        const savedPrediction = {
                          id: Date.now().toString(),
                          ...prediction,
                          timestamp: new Date().toISOString()
                        }
                        setSavedPredictions(prev => [...prev, savedPrediction])
                      }}
                    />
                  ) : isLoading ? (
                    <LoadingAnimation message="Generating Prediction..." />
                  ) : (
                    <div className="bg-card border border-border rounded-xl p-12 shadow-lg h-full flex items-center justify-center">
                      <div className="text-center space-y-4">
                        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto">
                          <Activity className="w-8 h-8 text-muted-foreground" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-foreground mb-2">
                            {!selectedPlayer ? 'Start by selecting a player' : 'Configure your bet parameters'}
                          </h3>
                          <p className="text-sm text-muted-foreground text-balance">
                            {!selectedPlayer 
                              ? 'Search for any NBA player to begin your prediction'
                              : 'Fill out the form to get your AI-powered prediction'
                            }
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              <SavedPredictions 
                predictions={savedPredictions}
                onRemovePrediction={(id) => {
                  setSavedPredictions(prev => prev.filter(p => p.id !== id))
                }}
              />
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border mt-20">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-sm text-muted-foreground">
            <p>GameLine © 2025 • AI-Powered NBA Predictions</p>
            <p className="mt-2 text-xs">For entertainment purposes only. Please gamble responsibly.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
