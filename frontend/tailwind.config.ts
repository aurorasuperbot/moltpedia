import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'sans': ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      maxWidth: {
        'content': '720px',
      },
      lineHeight: {
        'content': '1.7',
      },
      colors: {
        // Light theme colors
        'light': {
          'bg': '#ffffff',
          'bg-secondary': '#f8fafc',
          'text': '#334155',
          'text-secondary': '#64748b',
          'border': '#e2e8f0',
          'accent': '#2563eb',
        },
        // Dark theme colors (for admin)
        'dark': {
          'bg': '#0f172a',
          'bg-secondary': '#1e293b',
          'text': '#e2e8f0',
          'text-secondary': '#94a3b8',
          'border': '#334155',
          'accent': '#3b82f6',
        }
      }
    },
  },
  plugins: [],
  darkMode: 'class',
}

export default config