import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, LayoutGrid, Trash2, RefreshCw, Eye, Clock, Zap } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useProjects } from '@/hooks/useGenerationPolling'
import { projectsApi } from '@/api/client'
import EmptyState from '@/components/ui/EmptyState'
import ProgressBar from '@/components/ui/ProgressBar'
import {
  formatRelativeTime, statusBadgeClass, statusColor,
  formatCost, modelLabel, truncate
} from '@/utils/helpers'
import clsx from 'clsx'

function ProjectCard({ project, onDelete }) {
  const navigate = useNavigate()
  const [confirming, setConfirming] = useState(false)

  const progress = project.completed_panels / Math.max(project.total_panels, 1) * 100

  const handleClick = () => {
    if (project.status === 'generating') {
      navigate(`/projects/${project.project_id}/generating`)
    } else if (project.status === 'completed') {
      navigate(`/projects/${project.project_id}`)
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className="card-hover overflow-hidden relative"
      onClick={handleClick}
    >
      {/* Thumbnail strip */}
      <div className="relative h-36 bg-surface-2 overflow-hidden">
        {project.thumbnail_url ? (
          <img
            src={project.thumbnail_url.startsWith('http') ? project.thumbnail_url : `${import.meta.env.VITE_API_BASE_URL || 'https://storyframe-wctpi.ondigitalocean.app'}${project.thumbnail_url}`}
            alt={project.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="w-12 h-12 rounded-2xl bg-surface border border-border flex items-center justify-center">
              <LayoutGrid size={22} className="text-muted" />
            </div>
          </div>
        )}

        {/* Status overlay */}
        {project.status === 'generating' && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <div className="text-center">
              <div className="text-white font-semibold text-sm mb-1">
                {project.completed_panels}/{project.total_panels} panels
              </div>
              <div className="w-32 h-1 bg-white/20 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-warning rounded-full"
                  animate={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Status badge */}
        <div className="absolute top-2.5 left-2.5">
          <span className={clsx('badge', statusBadgeClass(project.status))}>
            {project.status}
          </span>
        </div>

        {/* Model badge */}
        <div className="absolute top-2.5 right-2.5 bg-black/60 backdrop-blur-sm
                        text-2xs text-muted px-2 py-0.5 rounded-full flex items-center gap-1">
          <Zap size={9} className="text-accent" />
          {modelLabel(project.image_model)}
        </div>
      </div>

      {/* Body */}
      <div className="p-4">
        <h3 className="font-semibold text-white text-sm mb-1 truncate">{project.title}</h3>
        <p className="text-muted text-xs mb-3 flex items-center gap-1.5">
          <Clock size={11} />
          {formatRelativeTime(project.created_at)}
        </p>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-2xs text-muted">
            <span>{project.total_panels} panels</span>
            <span>·</span>
            <span className="capitalize">{project.style_profile}</span>
            <span>·</span>
            <span>{formatCost(project.estimated_cost_usd)}</span>
          </div>

          {/* Actions */}
          <div className="flex gap-1" onClick={e => e.stopPropagation()}>
            {project.status === 'completed' && (
              <button
                onClick={() => navigate(`/projects/${project.project_id}`)}
                className="btn-ghost btn-icon p-1.5"
                title="View storyboard"
              >
                <Eye size={14} />
              </button>
            )}
            {confirming ? (
              <div className="flex gap-1">
                <button
                  onClick={() => { onDelete(project.project_id); setConfirming(false) }}
                  className="btn-danger btn-sm py-1"
                >
                  Delete
                </button>
                <button onClick={() => setConfirming(false)} className="btn-ghost btn-sm py-1">
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirming(true)}
                className="btn-ghost btn-icon p-1.5 text-muted hover:text-danger"
                title="Delete"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: projects = [], isLoading } = useProjects()

  const deleteMutation = useMutation({
    mutationFn: projectsApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
  })

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-end justify-between mb-8"
      >
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          <p className="text-muted text-sm mt-1">
            {projects.length
              ? `${projects.length} storyboard${projects.length !== 1 ? 's' : ''} · session`
              : 'Your AI-generated storyboards'}
          </p>
        </div>

        <button
          onClick={() => navigate('/create')}
          className="btn-primary btn-lg"
        >
          <Plus size={18} />
          New Storyboard
        </button>
      </motion.div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card h-56 skeleton" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <EmptyState
          icon={LayoutGrid}
          title="No storyboards yet"
          description="Paste a narrative and watch AI turn it into a cinematic visual storyboard in seconds."
          action={
            <button onClick={() => navigate('/create')} className="btn-primary btn-lg">
              <Plus size={18} />
              Create your first storyboard
            </button>
          }
        />
      ) : (
        <motion.div
          layout
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
        >
          <AnimatePresence>
            {projects.map(project => (
              <ProjectCard
                key={project.project_id}
                project={project}
                onDelete={(id) => deleteMutation.mutate(id)}
              />
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </div>
  )
}