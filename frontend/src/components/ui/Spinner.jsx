import React from 'react'
import clsx from 'clsx'

export default function Spinner({ size = 'md', className }) {
  const sz = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8', xl: 'w-12 h-12' }[size] || 'w-6 h-6'
  return (
    <div className={clsx('relative', sz, className)}>
      <div className={clsx('absolute inset-0 rounded-full border-2 border-border')} />
      <div className={clsx(
        'absolute inset-0 rounded-full border-2 border-transparent border-t-accent animate-spin'
      )} />
    </div>
  )
}