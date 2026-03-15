import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import AppLayout from '@/components/layout/AppLayout'
import PageLoader from '@/components/ui/PageLoader'

const Dashboard      = lazy(() => import('@/pages/Dashboard'))
const Create         = lazy(() => import('@/pages/Create'))
const Generating     = lazy(() => import('@/pages/Generating'))
const StoryboardView = lazy(() => import('@/pages/StoryboardView'))
const PanelEditor    = lazy(() => import('@/pages/PanelEditor'))
const ExportView     = lazy(() => import('@/pages/ExportView'))

export default function App() {
  return (
    <BrowserRouter>
      <AnimatePresence mode="wait">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Main app shell */}
            <Route element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="/create" element={<Create />} />
              <Route path="/projects/:id/generating" element={<Generating />} />
              <Route path="/projects/:id" element={<StoryboardView />} />
              <Route path="/projects/:id/edit/:panelIndex" element={<PanelEditor />} />
            </Route>

            {/* Full-screen export — no shell */}
            <Route path="/projects/:id/export" element={<ExportView />} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AnimatePresence>
    </BrowserRouter>
  )
}