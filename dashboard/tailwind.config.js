/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        crown:   { DEFAULT: "#C9973B", light: "#E8C06A", dark: "#9A6E24" },
        discord: { DEFAULT: "#5865F2", dark: "#4752C4" },
        surface: {
          50:  "#F5F3EE",
          100: "#EAE6DB",
          200: "#D5CDB7",
          800: "#1C1917",
          900: "#0F0D0B",
          950: "#080604",
        },
      },
      fontFamily: {
        display: ["'Cormorant Garamond'", "serif"],
        body:    ["'DM Sans'", "sans-serif"],
        mono:    ["'JetBrains Mono'", "monospace"],
      },
      backgroundImage: {
        "crown-gradient": "linear-gradient(135deg, #C9973B 0%, #E8C06A 50%, #C9973B 100%)",
        "dark-mesh": "radial-gradient(ellipse at 20% 50%, #1a1208 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, #1e160a 0%, transparent 50%)",
      },
      animation: {
        "fade-up":   "fadeUp 0.5s ease forwards",
        "shimmer":   "shimmer 2s infinite",
        "pulse-slow":"pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeUp: {
          "0%":   { opacity: 0, transform: "translateY(16px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
