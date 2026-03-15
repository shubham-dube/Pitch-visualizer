import React from 'react'
import { motion } from 'framer-motion'

export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-20 px-6 text-center"
    >
      <div className="w-16 h-16 rounded-2xl bg-surface border border-border flex items-center justify-center mb-5">
        <Icon size={28} className="text-muted" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-muted text-sm max-w-xs leading-relaxed mb-6">{description}</p>
      {action}
    </motion.div>
  )
}