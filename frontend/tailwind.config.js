/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { 50: "#eef4ff", 500: "#2563eb", 600: "#1d4ed8", 700: "#1e40af" },
        ink: "#0f172a",
      },
      borderRadius: { xl2: "1rem" },
    },
  },
  plugins: [],
};
