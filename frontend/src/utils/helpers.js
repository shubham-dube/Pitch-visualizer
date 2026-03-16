import { formatDistanceToNow, format } from 'date-fns'

export const formatRelativeTime = (dateStr) => {
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
  } catch {
    return dateStr
  }
}

export const formatDate = (dateStr) => {
  try {
    return format(new Date(dateStr), 'MMM d, yyyy')
  } catch {
    return dateStr
  }
}

export const formatCost = (usd) => {
  if (!usd || usd < 0.001) return '$0.00'
  if (usd < 0.01) return `$${(usd * 100).toFixed(1)}¢`
  return `$${usd.toFixed(3)}`
}

export const formatDuration = (ms) => {
  if (!ms) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export const arcTypeLabel = (arc) =>
  arc?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || '—'

export const intensityColor = (intensity) => {
  if (intensity >= 0.7) return 'text-danger'
  if (intensity >= 0.4) return 'text-warning'
  return 'text-success'
}

export const intensityBg = (intensity) => {
  if (intensity >= 0.7) return 'bg-danger'
  if (intensity >= 0.4) return 'bg-warning'
  return 'bg-success'
}

export const statusColor = (status) => ({
  queued:     'text-muted',
  generating: 'text-warning',
  completed:  'text-success',
  failed:     'text-danger',
}[status] || 'text-muted')

export const statusBadgeClass = (status) => ({
  queued:     'badge-muted',
  generating: 'badge-warning',
  completed:  'badge-success',
  failed:     'badge-danger',
}[status] || 'badge-muted')

export const roleBadgeColor = (role) => ({
  setup:      'bg-blue-500/15 text-blue-400',
  tension:    'bg-danger/15 text-danger',
  climax:     'bg-orange-500/15 text-orange-400',
  resolution: 'bg-success/15 text-success',
  cta:        'bg-accent/15 text-accent',
  context:    'bg-white/5 text-muted',
}[role] || 'bg-white/5 text-muted')

export const modelLabel = (model) => ({
  dalle3:  'DALL-E 3',
  gemini:  'Imagen 3',
}[model] || model)

export const truncate = (str, max = 80) =>
  str?.length > max ? `${str.slice(0, max)}…` : str


export const imageUrl = (path) => {
  if (!path) return null

  if (path.startsWith('http')) return path

  const base = import.meta.env.VITE_API_BASE_URL || 'https://storyframe-wctpi.ondigitalocean.app'

  return `${base}${path}`
}