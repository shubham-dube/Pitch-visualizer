import { create } from 'zustand'

export const useGenerationStore = create((set, get) => ({
  // Active polling project
  activeProjectId: null,
  isPolling: false,
  completedPanels: [],
  progress: null,
  status: null,

  setActiveProject: (id) =>
    set({ activeProjectId: id, completedPanels: [], progress: null, status: null }),

  setPolling: (v) => set({ isPolling: v }),

  updateFromStatus: (statusData) =>
    set({
      status: statusData.status,
      progress: statusData.progress,
      completedPanels: statusData.completed_panels || [],
    }),

  clearActive: () =>
    set({ activeProjectId: null, isPolling: false, completedPanels: [], progress: null, status: null }),
}))

export const useUIStore = create((set) => ({
  sidebarOpen: false,
  selectedStyle: 'cinematic',
  selectedModel: 'dalle3',
  panelLayout: 'grid',         // 'grid' | 'list'

  setSidebarOpen: (v) => set({ sidebarOpen: v }),
  setSelectedStyle: (s) => set({ selectedStyle: s }),
  setSelectedModel: (m) => set({ selectedModel: m }),
  setPanelLayout: (l) => set({ panelLayout: l }),
}))