import React from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'

const stages = ['Segmenting text…', 'Detecting narrative arc…', 'Engineering prompt…', 'Generating image…']

export default function PanelSkeleton({ index = 0, stage = null }) {
  const stageLabel = stage || stages[Math.min(index % stages.length, stages.length - 1)]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07 }}
      className="card overflow-hidden"
    >
      {/* Image placeholder */}
      <div className="relative aspect-video bg-surface-2 overflow-hidden">
        <div className="absolute inset-0 skeleton" />
        {/* Shimmer pulse */}
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
          <div className="flex gap-1">
            {[0,1,2].map(i => (
              <motion.div
                key={i}
                className="w-1.5 h-6 rounded-full bg-accent/30"
                animate={{ scaleY: [0.4, 1, 0.4] }}
                transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }}
              />
            ))}
          </div>
          <p className="text-2xs text-muted font-medium tracking-wide">{stageLabel}</p>
        </div>
        {/* Panel number badge */}
        <div className="absolute top-3 left-3 bg-black/50 backdrop-blur-sm text-muted
                        text-2xs font-bold px-2 py-1 rounded-full">
          Panel {index + 1}
        </div>
      </div>

      {/* Body skeleton */}
      <div className="p-4 space-y-3">
        <div className="flex gap-2">
          <div className="skeleton h-5 w-16 rounded-full" />
          <div className="skeleton h-5 w-20 rounded-full" />
        </div>
        <div className="skeleton h-5 w-3/4 rounded-lg" />
        <div className="space-y-2">
          <div className="skeleton h-3 w-full rounded" />
          <div className="skeleton h-3 w-5/6 rounded" />
        </div>
        <div className="flex gap-2">
          {[0,1,2].map(i => (
            <div key={i} className="skeleton w-5 h-5 rounded-full" />
          ))}
        </div>
      </div>
    </motion.div>
  )
}