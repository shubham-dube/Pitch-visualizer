import React, { useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, ArrowRight, Clock, DollarSign, Activity } from 'lucide-react'
import { useGenerationPolling } from '@/hooks/useGenerationPolling'
import { useGenerationStore } from '@/stores/generationStore'
import PanelCard from '@/components/panels/PanelCard'
import PanelSkeleton from '@/components/panels/PanelSkeleton'
import ProgressBar from '@/components/ui/ProgressBar'
import { arcTypeLabel, formatCost } from '@/utils/helpers'
import clsx from 'clsx'

const STAGE_LABELS = {
  segmenting:        'Segmenting your text…',
  arc_detection:     'Detecting narrative arc with Claude…',
  prompt_engineering:'Engineering visual prompts…',
  image_generation:  'Generating images…',
  assembling:        'Assembling storyboard…',
  done:              'Complete!',
}

function GenerationHeader({ title, progress, status }) {
  const elapsed = progress?.elapsed_seconds || 0
  const mm = String(Math.floor(elapsed / 60)).padStart(2, '0')
  const ss = String(Math.floor(elapsed % 60)).padStart(2, '0')

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-1">
        <motion.div
          animate={{ rotate: status === 'completed' ? 0 : 360 }}
          transition={{ duration: 2, repeat: status !== 'completed' ? Infinity : 0, ease: 'linear' }}
          className="w-5 h-5 rounded-full border-2 border-t-accent border-border"
        />
        <span className="text-2xs text-muted uppercase tracking-wider font-semibold">
          {status === 'completed' ? 'Complete' : 'Generating'}
        </span>
      </div>
      <h1 className="text-2xl font-bold text-white truncate">{title}</h1>

      {/* Progress bar */}
      <div className="mt-4">
        <ProgressBar
          percent={progress?.percent || 0}
          label={STAGE_LABELS[progress?.current_stage] || 'Starting…'}
          sublabel={`${progress?.completed_panels || 0}/${progress?.total_panels || '?'} panels · ${mm}:${ss}`}
          className="mb-0"
        />
      </div>
    </div>
  )
}

export default function Generating() {
  const { id } = useParams()
  const navigate = useNavigate()
  const bottomRef = useRef(null)

  const completedPanels = useGenerationStore(s => s.completedPanels)
  const progress        = useGenerationStore(s => s.progress)
  const status          = useGenerationStore(s => s.status)

  const { statusData } = useGenerationPolling(id, {
    onComplete: (data) => {
      if (data.status === 'completed') {
        setTimeout(() => navigate(`/projects/${id}`), 1500)
      }
    },
  })

  const project = statusData
  const totalPanels  = progress?.total_panels || 5
  const donePanels   = completedPanels.filter(p => p.status === 'done')
  const failedPanels = completedPanels.filter(p => p.status === 'failed')

  // Render grid: done panels + skeletons for remaining
  const skeletonCount = Math.max(0, totalPanels - donePanels.length)

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Header */}
      <GenerationHeader
        title={project?.title || 'Generating Storyboard…'}
        progress={progress}
        status={status}
      />

      {/* Stats bar */}
      {donePanels.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-wrap gap-4 mb-6 text-sm text-muted"
        >
          <div className="flex items-center gap-1.5">
            <Activity size={13} className="text-accent" />
            <span>{donePanels.length} of {totalPanels} panels complete</span>
          </div>
          {progress?.estimated_remaining_seconds && (
            <div className="flex items-center gap-1.5">
              <Clock size={13} />
              <span>~{Math.ceil(progress.estimated_remaining_seconds)}s remaining</span>
            </div>
          )}
        </motion.div>
      )}

      {/* Panel Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* Completed panels */}
        <AnimatePresence>
          {donePanels.map(panel => (
            <PanelCard
              key={panel.panel_index}
              panel={panel}
              projectId={id}
              totalPanels={totalPanels}
              showActions={false}
            />
          ))}
        </AnimatePresence>

        {/* Skeletons for remaining */}
        {status !== 'completed' && status !== 'failed' &&
          [...Array(skeletonCount)].map((_, i) => (
            <PanelSkeleton
              key={`skeleton-${i}`}
              index={donePanels.length + i}
              stage={STAGE_LABELS[progress?.current_stage]}
            />
          ))
        }
      </div>

      {/* Completion CTA */}
      <AnimatePresence>
        {status === 'completed' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 text-center"
          >
            <div className="card inline-flex flex-col items-center gap-4 px-8 py-6">
              <div className="text-4xl">🎉</div>
              <div>
                <p className="text-white font-bold text-lg">Your storyboard is ready!</p>
                <p className="text-muted text-sm mt-1">
                  {donePanels.length} panels generated
                </p>
              </div>
              <button
                onClick={() => navigate(`/projects/${id}`)}
                className="btn-primary btn-lg"
              >
                View Storyboard <ArrowRight size={18} />
              </button>
            </div>
          </motion.div>
        )}

        {status === 'failed' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 text-center"
          >
            <div className="card inline-flex flex-col items-center gap-3 px-8 py-6 border-danger/20">
              <p className="text-danger font-semibold">Generation failed</p>
              <p className="text-muted text-sm">{statusData?.error || 'An error occurred.'}</p>
              <button onClick={() => navigate('/')} className="btn-secondary">
                Back to Dashboard
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div ref={bottomRef} />
    </div>
  )
}