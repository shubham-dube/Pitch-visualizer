import React from 'react'
import { motion } from 'framer-motion'
import { Check } from 'lucide-react'
import clsx from 'clsx'
import { useStylesAndModels } from '@/hooks/useGenerationPolling'

const STYLE_GRADIENTS = {
  corporate:    'from-blue-900/50 to-slate-800/50',
  cinematic:    'from-amber-900/50 to-slate-900/50',
  storybook:    'from-pink-900/50 to-purple-900/50',
  minimal:      'from-slate-800/50 to-slate-900/50',
  futuristic:   'from-cyan-900/50 to-purple-900/50',
  documentary:  'from-orange-900/50 to-slate-900/50',
}

const STYLE_EMOJIS = {
  corporate:    '🏢',
  cinematic:    '🎬',
  storybook:    '📖',
  minimal:      '◽',
  futuristic:   '🚀',
  documentary:  '📷',
}

export default function StyleSelector({ value, onChange }) {
  const { styles } = useStylesAndModels()

  const items = styles.length ? styles : [
    { id: 'corporate',   display_name: 'Corporate',   description: 'Clean & professional', visual_vibe: 'Boardrooms, trust' },
    { id: 'cinematic',   display_name: 'Cinematic',   description: 'Dramatic & film-quality', visual_vibe: 'Golden hour, epic' },
    { id: 'storybook',   display_name: 'Storybook',   description: 'Warm & illustrated', visual_vibe: 'Watercolour, whimsical' },
    { id: 'minimal',     display_name: 'Minimal',     description: 'Clean & geometric', visual_vibe: 'Swiss design, space' },
    { id: 'futuristic',  display_name: 'Futuristic',  description: 'Dark & neon-lit', visual_vibe: 'Cyberpunk, holographic' },
    { id: 'documentary', display_name: 'Documentary', description: 'Authentic & candid', visual_vibe: 'Natural light, real' },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {items.map((style, i) => {
        const isActive = value === style.id
        return (
          <motion.button
            key={style.id}
            type="button"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onChange(style.id)}
            className={clsx(
              'relative text-left rounded-2xl border p-4 transition-all duration-150',
              isActive
                ? 'border-accent bg-accent/10 shadow-accent'
                : 'border-border bg-surface hover:border-border-light hover:bg-surface-2'
            )}
          >
            {/* Gradient bg */}
            <div className={clsx(
              'absolute inset-0 rounded-2xl bg-gradient-to-br opacity-30',
              STYLE_GRADIENTS[style.id] || 'from-surface to-surface-2'
            )} />

            <div className="relative">
              <div className="flex items-start justify-between mb-2">
                <span className="text-2xl">{STYLE_EMOJIS[style.id] || '🎨'}</span>
                {isActive && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-5 h-5 rounded-full bg-accent flex items-center justify-center"
                  >
                    <Check size={11} className="text-white" />
                  </motion.div>
                )}
              </div>
              <p className="font-semibold text-white text-sm">{style.display_name}</p>
              <p className="text-muted text-2xs mt-0.5 leading-relaxed">{style.visual_vibe}</p>
            </div>
          </motion.button>
        )
      })}
    </div>
  )
}