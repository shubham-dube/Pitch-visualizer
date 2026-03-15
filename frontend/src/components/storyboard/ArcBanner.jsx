import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp } from 'lucide-react'
import clsx from 'clsx'
import { arcTypeLabel, roleBadgeColor } from '@/utils/helpers'

const ARC_ICONS = {
  problem_solution: '🔧',
  journey:          '🗺️',
  transformation:   '✨',
  comparison:       '⚖️',
  timeline:         '📅',
  inspirational:    '🚀',
}

const ROLE_ORDER = ['setup', 'tension', 'climax', 'resolution', 'cta', 'context']

function ArcNode({ panel, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.06 }}
      className="flex flex-col items-center gap-1.5 min-w-0"
    >
      <div className={clsx(
        'w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold shrink-0',
        panel.intensity >= 0.7 ? 'border-danger text-danger bg-danger/10' :
        panel.intensity >= 0.4 ? 'border-warning text-warning bg-warning/10' :
        'border-success text-success bg-success/10'
      )}>
        {panel.panel_index + 1}
      </div>
      <span className={clsx('badge text-2xs', roleBadgeColor(panel.panel_role))}>
        {panel.panel_role}
      </span>
    </motion.div>
  )
}

function ArcConnector({ intensity }) {
  return (
    <div className="flex-1 flex items-center px-1">
      <div className="w-full h-px bg-gradient-to-r from-border to-border-light opacity-40" />
    </div>
  )
}

export default function ArcBanner({ storyboard }) {
  if (!storyboard) return null
  const { panels, overall_arc } = storyboard
  if (!panels?.length) return null

  const icon = ARC_ICONS[overall_arc] || '✦'

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card px-5 py-4 mb-6"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-xl bg-accent/15 flex items-center justify-center text-lg">
          {icon}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp size={13} className="text-accent" />
            <span className="text-2xs text-muted uppercase tracking-wider font-semibold">Narrative Arc</span>
          </div>
          <p className="text-sm font-semibold text-white">{arcTypeLabel(overall_arc)}</p>
        </div>
      </div>

      {/* Arc flow visualization */}
      <div className="flex items-start gap-0 overflow-x-auto no-scrollbar pb-1">
        {panels.map((panel, i) => (
          <React.Fragment key={panel.panel_index}>
            <ArcNode panel={panel} index={i} />
            {i < panels.length - 1 && <ArcConnector intensity={panel.intensity} />}
          </React.Fragment>
        ))}
      </div>
    </motion.div>
  )
}