import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, RefreshCw, Eye, Save, Wand2, ImageOff, ChevronLeft, ChevronRight
} from 'lucide-react'
import { useProjectDetail } from '@/hooks/useGenerationPolling'
import { panelsApi } from '@/api/client'
import { imageUrl, roleBadgeColor, intensityBg, arcTypeLabel, formatDuration, formatCost } from '@/utils/helpers'
import ProgressBar from '@/components/ui/ProgressBar'
import Spinner from '@/components/ui/Spinner'
import clsx from 'clsx'

export default function PanelEditor() {
  const { id, panelIndex } = useParams()
  const panelIdx = parseInt(panelIndex, 10)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: project, isLoading } = useProjectDetail(id)
  const [prompt, setPrompt] = useState('')
  const [preview, setPreview] = useState(null)
  const [imgError, setImgError] = useState(false)

  const panel = project?.storyboard?.panels?.find(p => p.panel_index === panelIdx)
  const panels = project?.storyboard?.panels || []
  const sortedPanels = [...panels].sort((a, b) => a.panel_index - b.panel_index)
  const totalPanels = sortedPanels.length

  useEffect(() => {
    if (panel) {
      setPrompt(panel.engineered_prompt || panel.visual_prompt || '')
      setPreview(null)
      setImgError(false)
    }
  }, [panel?.panel_index])

  const saveMutation = useMutation({
    mutationFn: () => panelsApi.updatePrompt(id, panelIdx, prompt),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['project', id] }),
  })

  const regenMutation = useMutation({
    mutationFn: () => panelsApi.regenerate(id, panelIdx, { prompt_override: prompt || undefined }),
    onSuccess: () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['project', id] })
      }, 3000)
    },
  })

  const previewMutation = useMutation({
    mutationFn: () => panelsApi.previewPrompt({
      text: panel?.original_text || '',
      style_profile: project?.style_profile || 'cinematic',
      panel_role: panel?.panel_role || 'context',
      intensity: panel?.intensity || 0.5,
      dominant_emotion: panel?.dominant_emotion || 'neutral',
    }),
    onSuccess: (data) => setPreview(data),
  })

  const goToPanel = (idx) => navigate(`/projects/${id}/edit/${idx}`)

  if (isLoading) return (
    <div className="flex items-center justify-center min-h-screen">
      <Spinner size="lg" />
    </div>
  )

  if (!panel) return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <p className="text-muted">Panel not found.</p>
      <button onClick={() => navigate(`/projects/${id}`)} className="btn-secondary">Back</button>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-6"
      >
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(`/projects/${id}`)} className="btn-ghost">
            <ArrowLeft size={16} />
          </button>
          <div>
            <h1 className="text-lg font-bold text-white">Edit Panel {panelIdx + 1}</h1>
            <p className="text-muted text-xs">{project?.title}</p>
          </div>
        </div>

        {/* Panel navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => goToPanel(panelIdx - 1)}
            disabled={panelIdx === 0}
            className="btn-ghost btn-icon"
          >
            <ChevronLeft size={18} />
          </button>
          <span className="text-sm text-muted w-16 text-center">
            {panelIdx + 1} / {totalPanels}
          </span>
          <button
            onClick={() => goToPanel(panelIdx + 1)}
            disabled={panelIdx >= totalPanels - 1}
            className="btn-ghost btn-icon"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </motion.div>

      {/* Main layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Image */}
        <div className="space-y-4">
          <div className="relative aspect-video rounded-2xl overflow-hidden bg-surface-2 border border-border">
            {panel.image_url && !imgError ? (
              <motion.img
                key={panel.image_url}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                src={imageUrl(panel.image_url)}
                alt={panel.scene_title}
                className="w-full h-full object-cover"
                onError={() => setImgError(true)}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-muted">
                <ImageOff size={32} />
              </div>
            )}
            {regenMutation.isPending && (
              <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                <div className="text-center">
                  <Spinner size="lg" className="mx-auto mb-3" />
                  <p className="text-white text-sm">Regenerating…</p>
                </div>
              </div>
            )}
          </div>

          {/* Panel metadata */}
          <div className="card p-4 space-y-3 text-sm">
            <h3 className="font-semibold text-white">{panel.scene_title}</h3>

            <div className="flex flex-wrap gap-2">
              <span className={clsx('badge', roleBadgeColor(panel.panel_role))}>
                {panel.panel_role}
              </span>
              <span className="badge badge-muted">{panel.dominant_emotion}</span>
              {panel.mood && <span className="badge badge-muted">{panel.mood}</span>}
            </div>

            <div>
              <p className="text-2xs text-muted uppercase tracking-wider mb-1.5">Intensity</p>
              <ProgressBar percent={Math.round(panel.intensity * 100)} />
            </div>

            {panel.color_palette?.length > 0 && (
              <div>
                <p className="text-2xs text-muted uppercase tracking-wider mb-1.5">Color palette</p>
                <div className="flex gap-2">
                  {panel.color_palette.map((c, i) => (
                    <div key={i} className="w-6 h-6 rounded-full border-2 border-white/10"
                         style={{ background: c }} title={c} />
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2 text-xs text-muted pt-1 border-t border-border">
              <span>Gen time: {formatDuration(panel.generation_time_ms)}</span>
              <span>Cost: {formatCost(panel.estimated_cost_usd)}</span>
              <span>Model: {panel.model_used === 'dalle3' ? 'DALL-E 3' : 'Imagen 3'}</span>
              {panel.retry_count > 0 && <span>Retries: {panel.retry_count}</span>}
            </div>
          </div>
        </div>

        {/* Right: Prompt editor */}
        <div className="space-y-4">
          {/* Original text */}
          <div className="card p-4">
            <p className="text-2xs text-muted uppercase tracking-wider mb-2">Original text</p>
            <p className="text-sm text-slate-300 leading-relaxed">{panel.original_text}</p>
          </div>

          {/* Prompt editor */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="label mb-0">Engineered visual prompt</label>
              <button
                onClick={() => previewMutation.mutate()}
                disabled={previewMutation.isPending}
                className="btn-ghost btn-sm gap-1"
              >
                {previewMutation.isPending ? <Spinner size="sm" /> : <Eye size={12} />}
                Preview
              </button>
            </div>
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              className="textarea h-40 font-mono text-xs"
              placeholder="Edit the visual prompt that will be sent to the image model…"
            />
            <p className="text-2xs text-muted mt-1">
              {prompt.length} chars · Style suffix is automatically appended on generation
            </p>
          </div>

          {/* Preview result */}
          {preview && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-4 border-accent/20"
            >
              <p className="text-2xs text-accent uppercase tracking-wider mb-2 flex items-center gap-1">
                <Wand2 size={11} /> Claude's prompt preview
              </p>
              <p className="font-semibold text-white text-sm mb-1">{preview.scene_title}</p>
              <p className="text-muted text-xs leading-relaxed mb-3">{preview.visual_prompt}</p>
              {preview.key_elements?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {preview.key_elements.map((el, i) => (
                    <span key={i} className="badge badge-muted">{el}</span>
                  ))}
                </div>
              )}
              <button
                onClick={() => setPrompt(preview.visual_prompt)}
                className="btn-ghost btn-sm mt-3 text-accent"
              >
                Use this prompt
              </button>
            </motion.div>
          )}

          {/* DALL-E revised prompt */}
          {panel.dalle_revised_prompt && panel.dalle_revised_prompt !== panel.visual_prompt && (
            <div className="card p-3">
              <p className="text-2xs text-muted uppercase tracking-wider mb-1.5">DALL-E revised prompt</p>
              <p className="text-xs text-muted italic leading-relaxed">{panel.dalle_revised_prompt}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || prompt === panel.engineered_prompt}
              className="btn-secondary flex-1 justify-center"
            >
              {saveMutation.isPending ? <Spinner size="sm" /> : <Save size={14} />}
              Save Prompt
            </button>
            <button
              onClick={() => regenMutation.mutate()}
              disabled={regenMutation.isPending}
              className="btn-primary flex-1 justify-center"
            >
              {regenMutation.isPending ? <Spinner size="sm" /> : <RefreshCw size={14} />}
              Regenerate Image
            </button>
          </div>

          {(saveMutation.isSuccess) && (
            <p className="text-success text-xs text-center">Prompt saved.</p>
          )}
          {(regenMutation.isSuccess) && (
            <p className="text-success text-xs text-center">Regeneration started. Refresh in a few seconds.</p>
          )}
          {(regenMutation.isError || saveMutation.isError) && (
            <p className="text-danger text-xs text-center">
              {regenMutation.error?.userMessage || saveMutation.error?.userMessage || 'An error occurred.'}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}