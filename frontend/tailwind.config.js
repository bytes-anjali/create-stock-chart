/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        yt: { red: "#FF0000", dark: "#0F0F0F", card: "#1F1F1F", border: "#3F3F3F" },
      },
    },
  },
  plugins: [],
};
