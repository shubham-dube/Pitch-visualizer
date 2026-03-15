/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Brand palette
        primary:   { DEFAULT: '#0F172A', light: '#1E293B', lighter: '#263348' },
        accent:    { DEFAULT: '#6366F1', light: '#818CF8', dark: '#4F46E5' },
        success:   { DEFAULT: '#10B981', light: '#34D399', dark: '#059669' },
        warning:   { DEFAULT: '#F59E0B', light: '#FCD34D', dark: '#D97706' },
        danger:    { DEFAULT: '#EF4444', light: '#F87171', dark: '#DC2626' },
        surface:   { DEFAULT: '#1E293B', 2: '#263348', 3: '#2D3F55' },
        muted:     { DEFAULT: '#64748B', light: '#94A3B8' },
        border:    { DEFAULT: '#334155', light: '#475569' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.65rem', { lineHeight: '1rem' }],
      },
      animation: {
        'fade-in':      'fadeIn 0.4s ease-out forwards',
        'slide-up':     'slideUp 0.5s ease-out forwards',
        'slide-in-right': 'slideInRight 0.4s ease-out forwards',
        'pulse-slow':   'pulse 3s ease-in-out infinite',
        'shimmer':      'shimmer 1.8s ease-in-out infinite',
        'scale-in':     'scaleIn 0.3s ease-out forwards',
        'glow':         'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn:        { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp:       { from: { opacity: 0, transform: 'translateY(20px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        slideInRight:  { from: { opacity: 0, transform: 'translateX(20px)' }, to: { opacity: 1, transform: 'translateX(0)' } },
        shimmer:       { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        scaleIn:       { from: { opacity: 0, transform: 'scale(0.95)' }, to: { opacity: 1, transform: 'scale(1)' } },
        glow:          { from: { boxShadow: '0 0 5px rgba(99,102,241,0.3)' }, to: { boxShadow: '0 0 20px rgba(99,102,241,0.6)' } },
      },
      backdropBlur: { xs: '2px' },
      boxShadow: {
        'card':    '0 4px 24px rgba(0,0,0,0.3)',
        'card-hover': '0 8px 32px rgba(99,102,241,0.2)',
        'accent':  '0 0 0 3px rgba(99,102,241,0.3)',
        'inner-glow': 'inset 0 1px 0 rgba(255,255,255,0.06)',
      },
    },
  },
  plugins: [],
}