import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, Download, RefreshCw, LayoutGrid, List,
  ExternalLink, Zap, Clock, DollarSign, Share2
} from 'lucide-react'
import { useProjectDetail } from '@/hooks/useGenerationPolling'
import { panelsApi, exportsApi, projectsApi } from '@/api/client'
import PanelCard from '@/components/panels/PanelCard'
import ArcBanner from '@/components/storyboard/ArcBanner'
import Spinner from '@/components/ui/Spinner'
import { formatRelativeTime, formatCost, formatDuration, modelLabel, arcTypeLabel } from '@/utils/helpers'
import { useGenerationStore } from '@/stores/generationStore'
import clsx from 'clsx'

export default function StoryboardView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const setActiveProject = useGenerationStore(s => s.setActiveProject)
  const [layout, setLayout] = useState('grid')   // 'grid' | 'list'
  const [copied, setCopied] = useState(false)

  const { data: project, isLoading, isError } = useProjectDetail(id)

  const regenPanelMutation = useMutation({
    mutationFn: ({ panelIndex }) => panelsApi.regenerate(id, panelIndex),
    onSuccess: () => {
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['project', id] }), 3000)
    },
  })

  const regenAllMutation = useMutation({
    mutationFn: () => projectsApi.regenerate(id),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setActiveProject(id)
      navigate(`/projects/${id}/generating`)
    },
  })

  const handleShare = () => {
    navigator.clipboard?.writeText(window.location.href)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (isLoading) return (
    <div className="flex items-center justify-center min-h-screen">
      <Spinner size="lg" />
    </div>
  )

  if (isError || !project) return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <p className="text-danger">Failed to load project.</p>
      <button onClick={() => navigate('/')} className="btn-secondary">Back</button>
    </div>
  )

  const storyboard = project.storyboard
  const panels = storyboard?.panels || []
  const sortedPanels = [...panels].sort((a, b) => a.panel_index - b.panel_index)
  const totalTime = panels.reduce((sum, p) => sum + (p.generation_time_ms || 0), 0)

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Back + Title */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start justify-between gap-4 mb-6"
      >
        <div className="flex items-start gap-4 min-w-0">
          <button onClick={() => navigate('/')} className="btn-ghost mt-1 shrink-0">
            <ArrowLeft size={16} />
          </button>
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-white truncate">{project.title}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-muted">
              <span>{formatRelativeTime(project.created_at)}</span>
              <span>·</span>
              <span className="capitalize">{project.style_profile}</span>
              <span>·</span>
              <span>{modelLabel(project.image_model)}</span>
              <span>·</span>
              <span>{panels.length} panels</span>
              <span>·</span>
              <span>{formatCost(project.estimated_cost_usd)}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Layout toggle */}
          <div className="hidden sm:flex gap-1 bg-surface rounded-xl p-1 border border-border">
            <button
              onClick={() => setLayout('grid')}
              className={clsx('p-1.5 rounded-lg transition-colors', layout === 'grid' ? 'bg-accent/20 text-accent' : 'text-muted hover:text-slate-300')}
            >
              <LayoutGrid size={15} />
            </button>
            <button
              onClick={() => setLayout('list')}
              className={clsx('p-1.5 rounded-lg transition-colors', layout === 'list' ? 'bg-accent/20 text-accent' : 'text-muted hover:text-slate-300')}
            >
              <List size={15} />
            </button>
          </div>

          <button onClick={handleShare} className="btn-secondary btn-sm">
            <Share2 size={13} />
            {copied ? 'Copied!' : 'Share'}
          </button>

          <a
            href={exportsApi.htmlUrl(id)}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary btn-sm"
          >
            <Download size={13} />
            Export HTML
          </a>

          <button
            onClick={() => regenAllMutation.mutate()}
            disabled={regenAllMutation.isPending}
            className="btn-secondary btn-sm"
          >
            {regenAllMutation.isPending
              ? <Spinner size="sm" />
              : <RefreshCw size={13} />
            }
            Regenerate All
          </button>
        </div>
      </motion.div>

      {/* Stats strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {[
          { label: 'Panels',     value: panels.length, icon: LayoutGrid },
          { label: 'Arc',        value: arcTypeLabel(storyboard?.overall_arc), icon: Zap },
          { label: 'Gen time',   value: formatDuration(totalTime), icon: Clock },
          { label: 'Est. cost',  value: formatCost(project.estimated_cost_usd), icon: DollarSign },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="card px-4 py-3 flex items-center gap-3">
            <Icon size={15} className="text-accent shrink-0" />
            <div className="min-w-0">
              <p className="text-2xs text-muted uppercase tracking-wider">{label}</p>
              <p className="text-sm font-semibold text-white truncate">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Arc banner */}
      <ArcBanner storyboard={storyboard} />

      {/* Panels */}
      {sortedPanels.length === 0 ? (
        <p className="text-center text-muted py-16">No panels generated yet.</p>
      ) : (
        <motion.div
          layout
          className={clsx(
            layout === 'grid'
              ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5'
              : 'flex flex-col gap-4'
          )}
        >
          {sortedPanels.map(panel => (
            <PanelCard
              key={panel.panel_index}
              panel={panel}
              projectId={id}
              totalPanels={sortedPanels.length}
              onRegenerate={(idx) => regenPanelMutation.mutate({ panelIndex: idx })}
              className={layout === 'list' ? 'sm:flex sm:gap-5' : ''}
            />
          ))}
        </motion.div>
      )}

      {/* Export footer */}
      {panels.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-10 card px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-4"
        >
          <div>
            <p className="font-semibold text-white">Export your storyboard</p>
            <p className="text-muted text-sm mt-0.5">Save as a standalone HTML file or view the print version.</p>
          </div>
          <div className="flex gap-3">
            <a
              href={exportsApi.jsonUrl(id)}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary btn-sm"
            >
              <ExternalLink size={13} />
              Export JSON
            </a>
            <button
              onClick={() => navigate(`/projects/${id}/export`)}
              className="btn-primary btn-sm"
            >
              <Download size={13} />
              Print / PDF
            </button>
          </div>
        </motion.div>
      )}
    </div>
  )
}