/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aviation: {
          dark: '#0b0f17',
          panel: '#111827',
          card: '#162032',
          border: '#1f293d',
          accent: '#06b6d4',      // Cyan HUD style
          green: '#10b981',       // System OK
          amber: '#f59e0b',       // Warning
          red: '#ef4444',         // Failure
        }
      }
    },
  },
  plugins: [],
}
