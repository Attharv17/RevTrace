/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ── Navy brand palette ──────────────────────────────────────
        navy: {
          50:  "#EEF2FF",
          100: "#E0E7FF",
          200: "#C7D2FE",
          300: "#A5B4FC",
          400: "#818CF8",
          500: "#1B3A6B",   // PRIMARY
          600: "#162F57",
          700: "#112443",
          800: "#0C1A30",
          900: "#070F1C",
        },
        // ── Charcoal surface palette ────────────────────────────────
        charcoal: {
          50:  "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
          800: "#1E293B",
          900: "#0F172A",
          950: "#0A0F1E",
        },
        // ── Accent blues ────────────────────────────────────────────
        accent: {
          blue:       "#3B82F6",
          "blue-lt":  "#60A5FA",
          green:      "#10B981",
          "green-lt": "#34D399",
          amber:      "#F59E0B",
          red:        "#EF4444",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        card:    "0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04)",
        "card-md": "0 4px 12px rgba(0,0,0,.08)",
        "card-lg": "0 8px 24px rgba(0,0,0,.10)",
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
      },
      keyframes: {
        "fade-in": {
          "0%":   { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in": {
          "0%":   { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-in":  "fade-in 0.25s ease-out",
        "slide-in": "slide-in 0.2s ease-out",
      },
    },
  },
  plugins: [],
};
