import React, { createContext, useContext, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, AlertCircle, X } from 'lucide-react'
import clsx from 'clsx'

const ToastCtx = createContext(null)

let _id = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const show = useCallback((message, type = 'info', duration = 4000) => {
    const id = ++_id
    setToasts(prev => [...prev, { id, message, type }])
    if (duration > 0) setTimeout(() => dismiss(id), duration)
    return id
  }, [])

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastCtx.Provider value={{ show, dismiss }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full">
        <AnimatePresence>
          {toasts.map(toast => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 60, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 60, scale: 0.95 }}
              transition={{ duration: 0.25 }}
              className={clsx(
                'flex items-start gap-3 px-4 py-3 rounded-xl shadow-2xl border text-sm font-medium',
                {
                  success: 'bg-success/10 border-success/20 text-success',
                  error:   'bg-danger/10 border-danger/20 text-danger',
                  warning: 'bg-warning/10 border-warning/20 text-warning',
                  info:    'bg-accent/10 border-accent/20 text-accent',
                }[toast.type]
              )}
            >
              {toast.type === 'success' && <CheckCircle size={16} className="mt-0.5 shrink-0" />}
              {toast.type === 'error'   && <XCircle size={16} className="mt-0.5 shrink-0" />}
              {toast.type === 'warning' && <AlertCircle size={16} className="mt-0.5 shrink-0" />}
              {toast.type === 'info'    && <AlertCircle size={16} className="mt-0.5 shrink-0" />}
              <span className="flex-1">{toast.message}</span>
              <button
                onClick={() => dismiss(toast.id)}
                className="opacity-60 hover:opacity-100 transition-opacity"
              >
                <X size={14} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastCtx)
  if (!ctx) throw new Error('useToast must be inside ToastProvider')
  return ctx
}