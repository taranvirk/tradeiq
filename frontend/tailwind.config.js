/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#070b14",
        panel: "#0d1422",
        line: "#1b2739",
        accent: "#5eead4",
        positive: "#4ade80",
        negative: "#fb7185",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 32px rgba(94, 234, 212, 0.08)",
      },
    },
  },
  plugins: [],
};

