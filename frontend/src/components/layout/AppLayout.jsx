import React, { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles, LayoutGrid, Plus, Github, Menu, X, Zap, Activity
} from 'lucide-react'
import { useProjects } from '@/hooks/useGenerationPolling'
import { useGenerationStore } from '@/stores/generationStore'
import clsx from 'clsx'

function NavItem({ to, icon: Icon, label, badge }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
          isActive
            ? 'bg-accent/15 text-accent'
            : 'text-muted hover:text-slate-300 hover:bg-white/5'
        )
      }
    >
      <Icon size={18} />
      <span>{label}</span>
      {badge != null && (
        <span className="ml-auto bg-accent/20 text-accent text-2xs font-bold px-1.5 py-0.5 rounded-full">
          {badge}
        </span>
      )}
    </NavLink>
  )
}

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const { data: projects = [] } = useProjects()
  const isPolling = useGenerationStore(s => s.isPolling)
  const activeProjectId = useGenerationStore(s => s.activeProjectId)

  const generating = projects.filter(p => p.status === 'generating').length

  const sidebar = (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center shadow-lg">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <div className="font-bold text-white text-sm leading-tight">Pitch Visualizer</div>
            <div className="text-2xs text-muted">AI Storyboard Generator</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <NavItem to="/" icon={LayoutGrid} label="Projects" badge={projects.length || null} />

        {generating > 0 && (
          <NavItem to={`/projects/${activeProjectId}/generating`} icon={Activity} label="Generating..." badge={generating} />
        )}
      </nav>

      {/* Create CTA */}
      <div className="px-3 py-4 border-t border-border">
        <button
          onClick={() => navigate('/create')}
          className="btn-primary w-full justify-center py-2.5"
        >
          <Plus size={16} />
          New Storyboard
        </button>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border">
        <div className="flex items-center gap-2 text-muted">
          <Zap size={12} className="text-accent" />
          <span className="text-2xs">Claude + DALL-E 3 / Imagen 3</span>
        </div>
      </div>
    </div>
  )

  return (
    <div className="flex h-screen overflow-hidden bg-primary">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-60 flex-shrink-0 flex-col border-r border-border bg-surface/50 backdrop-blur-sm">
        {sidebar}
      </aside>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 28, stiffness: 300 }}
              className="lg:hidden fixed left-0 top-0 bottom-0 z-50 w-64 flex flex-col
                         border-r border-border bg-surface shadow-2xl"
            >
              <div className="flex items-center justify-between px-4 pt-4">
                <span className="font-bold text-white">Menu</span>
                <button onClick={() => setMobileOpen(false)} className="btn-ghost btn-icon p-1">
                  <X size={18} />
                </button>
              </div>
              {sidebar}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar (mobile) */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-border bg-surface/50">
          <button
            onClick={() => setMobileOpen(true)}
            className="btn-ghost btn-icon"
          >
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-accent" />
            <span className="font-bold text-white text-sm">Pitch Visualizer</span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}