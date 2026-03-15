import React from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'

export default function ProgressBar({ percent = 0, label, sublabel, className, color = 'accent' }) {
  const colorClass = {
    accent:  'bg-accent',
    success: 'bg-success',
    warning: 'bg-warning',
    danger:  'bg-danger',
  }[color] || 'bg-accent'

  return (
    <div className={clsx('w-full', className)}>
      {(label || sublabel) && (
        <div className="flex justify-between items-baseline mb-2">
          {label && <span className="text-sm text-slate-300">{label}</span>}
          {sublabel && <span className="text-xs text-muted">{sublabel}</span>}
        </div>
      )}
      <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
        <motion.div
          className={clsx('h-full rounded-full', colorClass)}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}