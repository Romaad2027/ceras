export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--md-sys-color-primary)',
          foreground: 'var(--md-sys-color-on-primary)',
          container: 'var(--md-sys-color-primary-container)',
          containerForeground: 'var(--md-sys-color-on-primary-container)',
        },
        secondary: {
          DEFAULT: 'var(--md-sys-color-secondary)',
          foreground: 'var(--md-sys-color-on-secondary)',
          container: 'var(--md-sys-color-secondary-container)',
          containerForeground: 'var(--md-sys-color-on-secondary-container)',
        },
        tertiary: {
          DEFAULT: 'var(--md-sys-color-tertiary)',
          foreground: 'var(--md-sys-color-on-tertiary)',
          container: 'var(--md-sys-color-tertiary-container)',
          containerForeground: 'var(--md-sys-color-on-tertiary-container)',
        },
        surface: {
          DEFAULT: 'var(--md-sys-color-surface)',
          variant: 'var(--md-sys-color-surface-variant)',
          foreground: 'var(--md-sys-color-on-surface)',
        },
        background: 'var(--md-sys-color-background)',
        outline: {
          DEFAULT: 'var(--md-sys-color-outline)',
          variant: 'var(--md-sys-color-outline-variant)',
        },
        error: {
          DEFAULT: 'var(--md-sys-color-error)',
          foreground: 'var(--md-sys-color-on-error)',
          container: 'var(--md-sys-color-error-container)',
          containerForeground: 'var(--md-sys-color-on-error-container)',
        },
      }
    },
  },
  plugins: [],
}
