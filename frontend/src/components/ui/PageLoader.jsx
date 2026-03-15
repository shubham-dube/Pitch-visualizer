import React from 'react'
import { Sparkles } from 'lucide-react'

export default function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-primary">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent to-purple-500
                        flex items-center justify-center animate-pulse-slow shadow-lg shadow-accent/30">
          <Sparkles size={22} className="text-white" />
        </div>
        <div className="text-muted text-sm">Loading…</div>
      </div>
    </div>
  )
}