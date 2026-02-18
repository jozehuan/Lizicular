/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
  safelist: [
    // Green (for completed/analyzed)
    'bg-green-100', 'text-green-800', 'border-green-200',
    'dark:bg-green-900/40', 'dark:text-green-300', 'dark:border-green-800',
    // Blue (for processing/pending)
    'bg-blue-100', 'text-blue-800', 'border-blue-200',
    'dark:bg-blue-900/40', 'dark:text-blue-300', 'dark:border-blue-800',
    // Red (for failed)
    'bg-red-100', 'text-red-800', 'border-red-200',
    'dark:bg-red-900/40', 'dark:text-red-300', 'dark:border-red-800',
    // Default/Muted (for draft/default)
    'bg-muted', 'text-muted-foreground', 'border-border',
    // Shadow classes
    'shadow-sm', 'shadow-md', 'shadow-lg', 'shadow-xl', 'shadow-2xl', 'shadow-inner', 'shadow-none',
  ],
}
