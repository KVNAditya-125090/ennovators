/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        google: {
          teal: {
            DEFAULT: '#1A73E8',
            dark: '#174EA6',
            light: '#4285F4',
            surface: '#E8F0FE'
          },
          blue: {
            DEFAULT: '#4285F4',
            light: '#E8F0FE',
            dark: '#1A73E8'
          },
          red: {
            DEFAULT: '#EA4335',
            light: '#FCE8E6'
          },
          yellow: {
            DEFAULT: '#FBBC04',
            light: '#FEF7E0'
          },
          green: {
            DEFAULT: '#34A853',
            light: '#E6F4EA'
          },
          gray: {
            50: '#F8F9FA',
            100: '#F1F3F4',
            200: '#E8EAED',
            300: '#DADCE0',
            400: '#BDC1C6',
            500: '#9AA0A6',
            600: '#70757A',
            700: '#5F6368',
            800: '#3C4043',
            900: '#202124'
          }
        }
      },
      fontFamily: {
        sans: ['Google Sans', 'Roboto', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif']
      }
    },
  },
  plugins: [],
}

