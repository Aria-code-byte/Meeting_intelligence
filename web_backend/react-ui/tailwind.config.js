/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#EEF8FC',
        primary: '#061B35',
        'primary-dark': '#08213F',
        secondary: '#536172',
        accent: {
          orange: '#FFA54D',
          red: '#FF6B6B',
          green: '#10B981',
        },
        border: '#D6E1EA',
        surface: {
          blue: '#DCEBFF',
          'blue-light': '#E9F3FF',
          orange: '#FFF5EB',
          red: '#FFE7E7',
        },
      },
      fontFamily: {
        sans: [
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"PingFang SC"',
          '"Microsoft YaHei"',
          'sans-serif',
        ],
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.25rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
}
