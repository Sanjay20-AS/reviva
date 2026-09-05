/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0a0a0f",
        card: "#0f0f16",
        border: "rgba(255,255,255,0.08)",
        muted: "#71717a",
      },
      borderRadius: {
        xl: "0.75rem",
      },
    },
  },
  plugins: [],
}
