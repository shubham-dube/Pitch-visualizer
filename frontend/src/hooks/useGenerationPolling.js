import { useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '@/api/client'
import { useGenerationStore } from '@/stores/generationStore'

const POLL_INTERVAL = 1500  // ms

export function useGenerationPolling(projectId, { onComplete, onPanelDone } = {}) {
  const queryClient = useQueryClient()
  const updateFromStatus = useGenerationStore(s => s.updateFromStatus)
  const setPolling = useGenerationStore(s => s.setPolling)

  const { data, isError } = useQuery({
    queryKey: ['project-status', projectId],
    queryFn: () => projectsApi.getStatus(projectId),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (!status || status === 'completed' || status === 'failed') return false
      return POLL_INTERVAL
    },
    refetchIntervalInBackground: true,
  })

  useEffect(() => {
    if (!data) return
    updateFromStatus(data)

    const done = data.status === 'completed' || data.status === 'failed'
    setPolling(!done)

    if (done) {
      // Invalidate project detail cache so viewer gets fresh data
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      onComplete?.(data)
    }
  }, [data])

  return { statusData: data, isError }
}

export function useProjectDetail(projectId) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId),
    enabled: !!projectId,
    staleTime: 10_000,
  })
}

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
    staleTime: 5_000,
  })
}

export function useStylesAndModels() {
  const { data: styles = [] } = useQuery({
    queryKey: ['styles'],
    queryFn: async () => {
      const { configApi } = await import('@/api/client')
      return configApi.styles()
    },
    staleTime: Infinity,
  })

  const { data: models = [] } = useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const { configApi } = await import('@/api/client')
      return configApi.models()
    },
    staleTime: Infinity,
  })

  return { styles, models }
}