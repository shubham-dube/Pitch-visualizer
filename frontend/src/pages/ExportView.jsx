import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Printer, ArrowLeft, Download } from 'lucide-react'
import { useProjectDetail } from '@/hooks/useGenerationPolling'
import { exportsApi, imageUrl } from '@/api/client'
import { arcTypeLabel, roleBadgeColor, formatDate } from '@/utils/helpers'
import Spinner from '@/components/ui/Spinner'
import clsx from 'clsx'

export default function ExportView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: project, isLoading } = useProjectDetail(id)

  if (isLoading) return (
    <div className="flex items-center justify-center min-h-screen bg-primary">
      <Spinner size="lg" />
    </div>
  )

  if (!project?.storyboard) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-primary gap-4">
      <p className="text-muted">Storyboard not ready.</p>
      <button onClick={() => navigate(`/projects/${id}`)} className="btn-secondary">Back</button>
    </div>
  )

  const panels = [...(project.storyboard.panels || [])].sort((a, b) => a.panel_index - b.panel_index)

  return (
    <>
      {/* Print controls — hidden when printing */}
      <div className="print:hidden fixed top-4 left-4 right-4 z-50 flex justify-between items-center
                      bg-surface/90 backdrop-blur-sm border border-border rounded-2xl px-4 py-2.5 shadow-xl">
        <button onClick={() => navigate(`/projects/${id}`)} className="btn-ghost btn-sm">
          <ArrowLeft size={14} /> Back
        </button>
        <span className="text-sm font-semibold text-white hidden sm:block">{project.title}</span>
        <div className="flex gap-2">
          <a
            href={exportsApi.htmlUrl(id)}
            className="btn-secondary btn-sm"
            download
          >
            <Download size={13} /> Download HTML
          </a>
          <button onClick={() => window.print()} className="btn-primary btn-sm">
            <Printer size={13} /> Print / Save PDF
          </button>
        </div>
      </div>

      {/* Print content */}
      <div className="min-h-screen bg-primary text-slate-300 pt-20 print:pt-0 pb-16 px-8 max-w-6xl mx-auto font-sans">
        {/* Header */}
        <div className="text-center mb-12 pb-8 border-b border-border">
          <div className="text-accent text-xs uppercase tracking-widest font-semibold mb-3">
            Pitch Visualizer
          </div>
          <h1 className="text-4xl font-bold text-white mb-3">{project.title}</h1>
          <div className="flex justify-center gap-6 text-sm text-muted flex-wrap">
            <span>Style: <span className="text-slate-300 capitalize">{project.style_profile}</span></span>
            <span>·</span>
            <span>Panels: <span className="text-slate-300">{panels.length}</span></span>
            <span>·</span>
            <span>Arc: <span className="text-slate-300">{arcTypeLabel(project.storyboard.overall_arc)}</span></span>
            <span>·</span>
            <span>{formatDate(project.created_at)}</span>
          </div>
        </div>

        {/* Panels grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
          {panels.map((panel, i) => (
            <motion.div
              key={panel.panel_index}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="break-inside-avoid"
            >
              {/* Image */}
              <div className="aspect-video rounded-2xl overflow-hidden bg-surface-2 mb-4 border border-border">
                {panel.image_url ? (
                  <img
                    src={imageUrl(panel.image_url)}
                    alt={panel.scene_title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-muted text-sm">
                    Image unavailable
                  </div>
                )}
              </div>

              {/* Panel info */}
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-muted text-xs">Panel {panel.panel_index + 1}</span>
                    <h3 className="font-bold text-white text-base leading-snug">{panel.scene_title}</h3>
                  </div>
                  <div className="flex gap-1.5 shrink-0 mt-1">
                    <span className={clsx('badge text-2xs', roleBadgeColor(panel.panel_role))}>
                      {panel.panel_role}
                    </span>
                  </div>
                </div>
                <p className="text-muted text-sm leading-relaxed">{panel.original_text}</p>
                {panel.color_palette?.length > 0 && (
                  <div className="flex gap-1.5 pt-1">
                    {panel.color_palette.map((c, i) => (
                      <div key={i} className="w-4 h-4 rounded-full border border-white/10"
                           style={{ background: c }} />
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-16 pt-6 border-t border-border text-center text-muted text-xs">
          Generated with Pitch Visualizer AI · {formatDate(project.created_at)}
        </div>
      </div>

      {/* Print-specific styles */}
      <style>{`
        @media print {
          body { background: white !important; color: #1a1a1a !important; }
          .text-white { color: #1a1a1a !important; }
          .text-slate-300, .text-muted { color: #555 !important; }
          .bg-primary { background: white !important; }
          .border-border { border-color: #e5e7eb !important; }
          .card, .rounded-2xl { box-shadow: none !important; }
        }
      `}</style>
    </>
  )
}