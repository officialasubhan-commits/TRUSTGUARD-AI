/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#080808',
          secondary: '#101010',
          surface: '#141414',
          elevated: '#181818',
          hover: '#1C1C1C',
          active: '#222222',
        },
        text: {
          primary: '#F5F5F5',
          secondary: '#A1A1A1',
          muted: '#666666',
          subtle: '#404040',
          white: '#FFFFFF',
        },
        border: {
          DEFAULT: '#292929',
          subtle: '#292929',
          strong: '#383838',
          active: '#525252',
          focus: '#F5F5F5',
        },
        status: {
          safe: {
            text: '#4ADE80',
            bg: '#052E16',
            border: '#166534',
          },
          suspicious: {
            text: '#FBBF24',
            bg: '#451A03',
            border: '#92400E',
          },
          malicious: {
            text: '#F87171',
            bg: '#450A0A',
            border: '#991B1B',
          },
          unknown: {
            text: '#A1A1A1',
            bg: '#141414',
            border: '#383838',
          },
        },
      },
      fontFamily: {
        sans: ['Geist Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['Geist Mono', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      letterSpacing: {
        tightest: '-0.04em',
        tighter: '-0.02em',
        tight: '-0.01em',
        normal: '0',
        wide: '0.02em',
        widest: '0.06em',
      },
      maxWidth: {
        'container-sm': '640px',
        'container-md': '896px',
        'container-lg': '1152px',
        'container-xl': '1344px',
      },
      transitionTimingFunction: {
        'editorial': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
}
