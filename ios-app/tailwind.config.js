/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        // iOS blue theme
        primary: {
          50: '#E6F2FF',
          100: '#CCE5FF',
          200: '#99CBFF',
          300: '#66B0FF',
          400: '#3396FF',
          500: '#007AFF',
          600: '#0066CC',
          700: '#004D99',
        },
        // Success/Recipe colors
        success: {
          50: '#E8F5E9',
          500: '#4CAF50',
          600: '#43A047',
        },
        // Warning/Expiring colors
        warning: {
          50: '#FFF3E0',
          500: '#FF9800',
          600: '#FB8C00',
        },
      },
    },
  },
  plugins: [],
};