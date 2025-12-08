/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: "#A25CF0",
        accentSoft: "#E4D7FF",
        softbg: "#F6F5FB"
      },
      boxShadow: {
        soft: "0 18px 45px rgba(15,23,42,0.08)"
      },
      borderRadius: {
        "2xl": "1.25rem",
        "3xl": "1.75rem"
      }
    }
  },
  plugins: []
};
