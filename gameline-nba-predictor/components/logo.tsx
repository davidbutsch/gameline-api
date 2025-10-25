"use client"

interface LogoProps {
  className?: string
  size?: "sm" | "md" | "lg"
}

export function Logo({ className = "", size = "md" }: LogoProps) {
  const sizeClasses = {
    sm: "w-6 h-6",
    md: "w-8 h-8", 
    lg: "w-12 h-12"
  }

  return (
    <div className={`relative ${sizeClasses[size]} ${className}`}>
      {/* Green Shape - Behind and to the left */}
      <div className="absolute inset-0 bg-green-500 rounded-full transform -translate-x-1 -translate-y-0.5 scale-90"></div>
      
      {/* Yellow Shape - Foreground, slightly irregular */}
      <div className="absolute inset-0 bg-yellow-400 rounded-full transform translate-x-0.5 translate-y-0.5 scale-105" 
           style={{ clipPath: 'polygon(20% 0%, 100% 0%, 100% 100%, 0% 100%, 0% 20%)' }}></div>
    </div>
  )
}
