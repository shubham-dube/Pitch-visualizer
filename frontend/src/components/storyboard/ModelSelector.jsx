import React from 'react'
import { motion } from 'framer-motion'
import { Check, Zap } from 'lucide-react'
import clsx from 'clsx'

const MODELS = [
  {
    id: 'dalle3',
    name: 'DALL-E 3',
    provider: 'OpenAI',
    description: 'Exceptional prompt adherence. Best for creative, dramatic styles.',
    speed: '~20s / panel',
    quality: 'Stunning HD',
    badge: 'Most Creative',
    badgeColor: 'badge-accent',
    icon: '◆',
    iconColor: 'text-green-400',
  },
  {
    id: 'gemini',
    name: 'Imagen 3',
    provider: 'Google Gemini',
    description: 'Ultra-photorealistic output. Best for corporate and documentary styles.',
    speed: '~15s / panel',
    quality: 'Photorealistic',
    badge: 'Most Realistic',
    badgeColor: 'badge-success',
    icon: '●',
    iconColor: 'text-blue-400',
  },
]

export default function ModelSelector({ value, onChange }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {MODELS.map((model, i) => {
        const isActive = value === model.id
        return (
          <motion.button
            key={model.id}
            type="button"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            onClick={() => onChange(model.id)}
            className={clsx(
              'relative text-left rounded-2xl border p-4 transition-all duration-150',
              isActive
                ? 'border-accent bg-accent/10 shadow-accent'
                : 'border-border bg-surface hover:border-border-light hover:bg-surface-2'
            )}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className={clsx('text-xl font-bold', model.iconColor)}>{model.icon}</span>
                <div>
                  <p className="font-bold text-white text-sm">{model.name}</p>
                  <p className="text-2xs text-muted">{model.provider}</p>
                </div>
              </div>
              {isActive
                ? <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}
                    className="w-5 h-5 rounded-full bg-accent flex items-center justify-center">
                    <Check size={11} className="text-white" />
                  </motion.div>
                : <span className={clsx('badge', model.badgeColor)}>{model.badge}</span>
              }
            </div>

            <p className="text-muted text-xs leading-relaxed mb-3">{model.description}</p>

            <div className="flex gap-3">
              <div className="flex items-center gap-1 text-2xs text-muted">
                <Zap size={10} className="text-accent" />
                {model.speed}
              </div>
              <div className="flex items-center gap-1 text-2xs text-muted">
                <span className="text-success">✦</span>
                {model.quality}
              </div>
            </div>
          </motion.button>
        )
      })}
    </div>
  )
}