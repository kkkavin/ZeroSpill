/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          dark: '#0a0d14',
          card: '#0f172a',
          border: '#1e293b',
          neon: '#06b6d4',
          alert: '#f43f5e',
          warning: '#f59e0b',
          success: '#10b981',
        }
      },
      animation: {
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(244, 63, 94, 0.4)' },
          '100%': { boxShadow: '0 0 20px rgba(244, 63, 94, 0.8)' },
        }
      }
    },
  },
  plugins: [],
}
