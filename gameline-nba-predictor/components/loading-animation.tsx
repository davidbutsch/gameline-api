"use client"

import { Logo } from "./logo"

interface LoadingAnimationProps {
  message?: string
}

export function LoadingAnimation({ message = "Analyzing Player Data..." }: LoadingAnimationProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-12 shadow-lg h-full flex items-center justify-center">
      <div className="text-center space-y-6">
        {/* Animated Logo */}
        <div className="flex justify-center">
          <div className="relative">
            <Logo size="lg" className="animate-pulse" />
            <div className="absolute inset-0 animate-spin">
              <div className="w-16 h-16 border-4 border-accent-primary/20 border-t-accent-primary rounded-full"></div>
            </div>
          </div>
        </div>
        
        {/* Loading Message */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-foreground">{message}</h3>
          <p className="text-sm text-muted-foreground">
            Our AI is analyzing player statistics, recent performance, and opponent data
          </p>
        </div>
        
        {/* Animated Progress Dots */}
        <div className="flex justify-center space-x-2">
          <div className="w-2 h-2 bg-accent-primary rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-accent-secondary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-accent-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        </div>
      </div>
    </div>
  )
}
