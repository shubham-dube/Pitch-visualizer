import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, Edit3, ImageOff, Zap } from 'lucide-react'
import clsx from 'clsx'
import { imageUrl, intensityBg, roleBadgeColor, truncate } from '@/utils/helpers'

function ColorPalette({ colors }) {
  if (!colors?.length) return null
  return (
    <div className="flex items-center gap-1.5">
      {colors.map((c, i) => (
        <div
          key={i}
          className="w-4 h-4 rounded-full border-2 border-white/10 shrink-0"
          style={{ background: c }}
          title={c}
        />
      ))}
    </div>
  )
}

function IntensityBar({ intensity }) {
  const pct = Math.round(intensity * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-surface-3 rounded-full overflow-hidden">
        <motion.div
          className={clsx('h-full rounded-full', intensityBg(intensity))}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>
      <span className="text-2xs text-muted w-8 text-right">{pct}%</span>
    </div>
  )
}

export default function PanelCard({
  panel,
  projectId,
  totalPanels,
  onRegenerate,
  showActions = true,
  className,
}) {
  const navigate = useNavigate()
  const [imgError, setImgError] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)

  const handleRegenerate = async (e) => {
    e.stopPropagation()
    setIsRegenerating(true)
    try {
      await onRegenerate?.(panel.panel_index)
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleEdit = (e) => {
    e.stopPropagation()
    navigate(`/projects/${projectId}/edit/${panel.panel_index}`)
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className={clsx('card overflow-hidden group', className)}
    >
      {/* ── Image ─────────────────────────────────────────────── */}
      <div className="relative aspect-video bg-surface-2 overflow-hidden">
        {panel.image_url && !imgError ? (
          <motion.img
            initial={{ scale: 1.04, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5 }}
            src={imageUrl(panel.image_url)}
            alt={panel.scene_title || `Panel ${panel.panel_index + 1}`}
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2 text-muted">
            <ImageOff size={28} />
            <span className="text-xs">Image unavailable</span>
          </div>
        )}

        {/* Overlay on hover */}
        {showActions && (
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100
                          transition-opacity duration-200 flex items-center justify-center gap-3">
            <button
              onClick={handleEdit}
              className="btn-secondary btn-sm gap-1.5"
            >
              <Edit3 size={13} /> Edit Prompt
            </button>
            <button
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className="btn-secondary btn-sm gap-1.5"
            >
              <RefreshCw size={13} className={clsx(isRegenerating && 'animate-spin')} />
              {isRegenerating ? 'Regenerating…' : 'Regenerate'}
            </button>
          </div>
        )}

        {/* Panel number */}
        <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-sm text-white
                        text-2xs font-bold px-2.5 py-1 rounded-full">
          {panel.panel_index + 1} / {totalPanels}
        </div>

        {/* Intensity strip */}
        <div
          className="absolute bottom-0 left-0 right-0 h-0.5 opacity-80"
          style={{
            background: panel.intensity >= 0.7
              ? 'linear-gradient(to right, #EF4444, transparent)'
              : panel.intensity >= 0.4
              ? 'linear-gradient(to right, #F59E0B, transparent)'
              : 'linear-gradient(to right, #10B981, transparent)',
          }}
        />

        {/* DALL-E / Gemini badge */}
        <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-sm text-2xs
                        text-muted px-2 py-0.5 rounded-full flex items-center gap-1">
          <Zap size={9} className="text-accent" />
          {panel.model_used === 'dalle3' ? 'DALL-E 3' : 'Imagen 3'}
        </div>

        {/* Failed state */}
        {panel.status === 'failed' && (
          <div className="absolute inset-0 bg-danger/10 flex items-center justify-center">
            <span className="text-danger text-xs font-medium bg-black/60 px-3 py-1 rounded-lg">
              Generation failed
            </span>
          </div>
        )}
      </div>

      {/* ── Body ──────────────────────────────────────────────── */}
      <div className="p-4">
        {/* Badges */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          <span className={clsx('badge text-2xs', roleBadgeColor(panel.panel_role))}>
            {panel.panel_role}
          </span>
          <span className="badge badge-muted text-2xs">
            {panel.dominant_emotion}
          </span>
          {panel.mood && (
            <span className="badge badge-muted text-2xs">
              {panel.mood}
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="font-semibold text-white text-sm mb-2 leading-snug">
          {panel.scene_title || `Panel ${panel.panel_index + 1}`}
        </h3>

        {/* Caption */}
        <p className="text-muted text-xs leading-relaxed mb-3">
          {truncate(panel.original_text, 100)}
        </p>

        {/* Intensity */}
        <div className="mb-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-2xs text-muted uppercase tracking-wider">Intensity</span>
          </div>
          <IntensityBar intensity={panel.intensity ?? 0.5} />
        </div>

        {/* Color palette */}
        {panel.color_palette?.length > 0 && (
          <ColorPalette colors={panel.color_palette} />
        )}
      </div>
    </motion.div>
  )
}