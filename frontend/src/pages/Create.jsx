import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ArrowRight, Sparkles, FileText, Palette, Settings2, Info } from 'lucide-react'
import { projectsApi } from '@/api/client'
import { useGenerationStore } from '@/stores/generationStore'
import StyleSelector from '@/components/storyboard/StyleSelector'
import ModelSelector from '@/components/storyboard/ModelSelector'
import Spinner from '@/components/ui/Spinner'
import clsx from 'clsx'

const schema = z.object({
  title:        z.string().min(1, 'Title is required').max(200),
  input_text:   z.string().min(50, 'Text must be at least 50 characters').max(5000),
  style_profile: z.string().default('cinematic'),
  image_model:  z.string().default('dalle3'),
  max_panels:   z.number().min(3).max(8).default(5),
  image_quality: z.string().default('hd'),
  detect_arc:   z.boolean().default(true),
})

const STEPS = [
  { id: 1, label: 'Your Story',  icon: FileText },
  { id: 2, label: 'Visual Style', icon: Palette },
  { id: 3, label: 'Settings',    icon: Settings2 },
]

const EXAMPLE_TEXTS = [
  "Acme Corp was drowning in disconnected systems, losing 3 hours per employee daily. Their team was frustrated and morale was plummeting. Then they discovered our platform — a single unified workspace that replaced 7 tools overnight. Within 90 days, productivity soared 40% and employee satisfaction hit an all-time high. Today, Acme is our fastest-growing enterprise client, expanding to 500 seats.",
  "In 2019, Maria started her bakery with $800 and a dream. The first year was brutal — 80-hour weeks, zero profit, and near bankruptcy. She almost gave up in March 2020. Instead, she pivoted online. A viral TikTok changed everything. By 2023, Sweet Maria's employs 12 people, ships nationwide, and was featured in Food & Wine magazine.",
]

function StepIndicator({ currentStep }) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {STEPS.map((step, i) => {
        const isActive = step.id === currentStep
        const isDone   = step.id < currentStep
        return (
          <React.Fragment key={step.id}>
            <div className="flex items-center gap-2">
              <div className={clsx(
                'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all',
                isDone   ? 'bg-success text-white' :
                isActive ? 'bg-accent text-white ring-4 ring-accent/20' :
                           'bg-surface border border-border text-muted'
              )}>
                {isDone ? '✓' : step.id}
              </div>
              <span className={clsx(
                'text-sm font-medium hidden sm:block transition-colors',
                isActive ? 'text-white' : isDone ? 'text-muted' : 'text-muted'
              )}>
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={clsx(
                'flex-1 h-px max-w-12 transition-colors',
                isDone ? 'bg-success/40' : 'bg-border'
              )} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}

export default function Create() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const setActiveProject = useGenerationStore(s => s.setActiveProject)
  const [step, setStep] = useState(1)

  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      style_profile: 'cinematic',
      image_model:   'dalle3',
      max_panels:    5,
      image_quality: 'hd',
      detect_arc:    true,
    },
  })

  const watchedText  = watch('input_text') || ''
  const watchedStyle = watch('style_profile')
  const watchedModel = watch('image_model')

  const createMutation = useMutation({
    mutationFn: (data) => projectsApi.create({
      title:         data.title,
      input_text:    data.input_text,
      style_profile: data.style_profile,
      options: {
        max_panels:    data.max_panels,
        image_quality: data.image_quality,
        detect_arc:    data.detect_arc,
        image_model:   data.image_model,
      },
    }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setActiveProject(res.project_id)
      navigate(`/projects/${res.project_id}/generating`)
    },
  })

  const charCount   = watchedText.length
  const charPercent = Math.min(100, (charCount / 5000) * 100)
  const wordCount   = watchedText.trim() ? watchedText.trim().split(/\s+/).length : 0

  const nextStep = () => setStep(s => Math.min(s + 1, 3))
  const prevStep = () => setStep(s => Math.max(s - 1, 1))

  const canProceed1 = watchedText.length >= 50 && !errors.input_text && !errors.title
  const canProceed2 = !!watchedStyle && !!watchedModel

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      {/* Back */}
      <button onClick={() => navigate('/')} className="btn-ghost mb-6 -ml-1">
        <ArrowLeft size={16} />
        Back to Projects
      </button>

      {/* Step indicator */}
      <StepIndicator currentStep={step} />

      <form onSubmit={handleSubmit(d => createMutation.mutate(d))}>
        <AnimatePresence mode="wait">
          {/* ── Step 1: Text Input ─────────────────────────────── */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-5"
            >
              <div>
                <h2 className="text-xl font-bold text-white mb-1">Your narrative</h2>
                <p className="text-muted text-sm">Paste a story, case study, or pitch. The AI will segment it into cinematic panels.</p>
              </div>

              {/* Title */}
              <div>
                <label className="label">Project title</label>
                <input
                  {...register('title')}
                  className="input"
                  placeholder="e.g. Acme Corp Success Story"
                />
                {errors.title && <p className="text-danger text-xs mt-1">{errors.title.message}</p>}
              </div>

              {/* Text */}
              <div>
                <div className="flex justify-between items-baseline mb-2">
                  <label className="label mb-0">Narrative text</label>
                  <span className={clsx('text-2xs', charCount < 50 ? 'text-muted' : charCount > 4500 ? 'text-warning' : 'text-success')}>
                    {wordCount} words · {charCount}/5000
                  </span>
                </div>
                <textarea
                  {...register('input_text')}
                  className="textarea h-44"
                  placeholder="Paste your narrative here — a customer success story, pitch, timeline, or any compelling text…"
                />
                {/* Char bar */}
                <div className="mt-1.5 h-0.5 bg-surface-2 rounded-full overflow-hidden">
                  <motion.div
                    className={clsx('h-full rounded-full transition-colors', charCount >= 50 ? 'bg-success' : 'bg-muted')}
                    animate={{ width: `${charPercent}%` }}
                  />
                </div>
                {errors.input_text && <p className="text-danger text-xs mt-1.5">{errors.input_text.message}</p>}
              </div>

              {/* Example texts */}
              <div>
                <p className="text-2xs text-muted uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Info size={11} /> Try an example
                </p>
                <div className="space-y-2">
                  {EXAMPLE_TEXTS.map((txt, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => {
                        setValue('input_text', txt)
                        setValue('title', i === 0 ? 'Acme Corp Success Story' : "Maria's Bakery Journey")
                      }}
                      className="w-full text-left card px-3 py-2.5 hover:border-accent/30 transition-colors"
                    >
                      <p className="text-xs text-muted line-clamp-2">{txt.slice(0, 120)}…</p>
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={nextStep}
                disabled={!canProceed1}
                className="btn-primary w-full justify-center py-3"
              >
                Choose Visual Style <ArrowRight size={16} />
              </button>
            </motion.div>
          )}

          {/* ── Step 2: Style & Model ──────────────────────────── */}
          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-xl font-bold text-white mb-1">Visual style</h2>
                <p className="text-muted text-sm">Choose the visual DNA for all panels. Applied consistently across the entire storyboard.</p>
              </div>

              <StyleSelector value={watchedStyle} onChange={v => setValue('style_profile', v)} />

              <div>
                <h3 className="text-sm font-semibold text-white mb-3">Image generation model</h3>
                <ModelSelector value={watchedModel} onChange={v => setValue('image_model', v)} />
              </div>

              <div className="flex gap-3">
                <button type="button" onClick={prevStep} className="btn-secondary flex-1 justify-center">
                  <ArrowLeft size={16} /> Back
                </button>
                <button type="button" onClick={nextStep} disabled={!canProceed2} className="btn-primary flex-1 justify-center">
                  Configure <ArrowRight size={16} />
                </button>
              </div>
            </motion.div>
          )}

          {/* ── Step 3: Options + Submit ───────────────────────── */}
          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-xl font-bold text-white mb-1">Generation settings</h2>
                <p className="text-muted text-sm">Fine-tune how many panels to generate and quality settings.</p>
              </div>

              {/* Panel count */}
              <div>
                <label className="label">Number of panels: <span className="text-accent">{watch('max_panels')}</span></label>
                <input
                  type="range" min={3} max={8} step={1}
                  {...register('max_panels', { valueAsNumber: true })}
                  className="w-full accent-accent"
                />
                <div className="flex justify-between text-2xs text-muted mt-1">
                  <span>3 (fast)</span><span>5 (recommended)</span><span>8 (detailed)</span>
                </div>
              </div>

              {/* Quality (DALL-E only) */}
              {watchedModel === 'dalle3' && (
                <div>
                  <label className="label">Image quality</label>
                  <div className="grid grid-cols-2 gap-3">
                    {['standard', 'hd'].map(q => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => setValue('image_quality', q)}
                        className={clsx(
                          'rounded-xl border p-3 text-sm font-medium transition-all',
                          watch('image_quality') === q
                            ? 'border-accent bg-accent/10 text-accent'
                            : 'border-border bg-surface text-muted hover:border-border-light'
                        )}
                      >
                        {q === 'hd' ? '✦ HD (recommended)' : 'Standard'}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Arc detection toggle */}
              <div className="flex items-center justify-between p-4 card">
                <div>
                  <p className="text-sm font-medium text-white">Narrative Arc Detection</p>
                  <p className="text-xs text-muted mt-0.5">Claude analyses story structure to guide visual tone per panel</p>
                </div>
                <button
                  type="button"
                  onClick={() => setValue('detect_arc', !watch('detect_arc'))}
                  className={clsx(
                    'relative w-11 h-6 rounded-full transition-colors duration-200',
                    watch('detect_arc') ? 'bg-accent' : 'bg-surface-3'
                  )}
                >
                  <motion.div
                    animate={{ x: watch('detect_arc') ? 20 : 2 }}
                    className="absolute top-1 w-4 h-4 rounded-full bg-white shadow"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                </button>
              </div>

              {/* Summary */}
              <div className="card p-4 space-y-2 text-sm">
                <p className="text-muted text-xs uppercase tracking-wider font-semibold mb-3">Summary</p>
                {[
                  ['Style',   watchedStyle],
                  ['Model',   watchedModel === 'dalle3' ? 'DALL-E 3' : 'Imagen 3'],
                  ['Panels',  watch('max_panels')],
                  ['Quality', watchedModel === 'dalle3' ? watch('image_quality').toUpperCase() : 'Auto'],
                  ['Arc Detection', watch('detect_arc') ? 'On' : 'Off'],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-muted capitalize">{k}</span>
                    <span className="text-white font-medium capitalize">{v}</span>
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <button type="button" onClick={prevStep} className="btn-secondary flex-1 justify-center">
                  <ArrowLeft size={16} /> Back
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="btn-primary flex-1 justify-center py-3 text-base"
                >
                  {createMutation.isPending
                    ? <><Spinner size="sm" /> Launching…</>
                    : <><Sparkles size={18} /> Generate Storyboard</>
                  }
                </button>
              </div>

              {createMutation.isError && (
                <p className="text-danger text-sm text-center">
                  {createMutation.error?.userMessage || 'Failed to create project. Check your API keys.'}
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </form>
    </div>
  )
}