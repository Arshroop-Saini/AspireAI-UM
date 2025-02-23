import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#FF4500",
          50: "#FFF2EC",
          100: "#FFE5D9",
          200: "#FFB899",
          300: "#FF8A59",
          400: "#FF5C1A",
          500: "#FF4500",
          600: "#CC3700",
          700: "#992900",
          800: "#661C00",
          900: "#330E00"
        },
        dark: {
          DEFAULT: "#1A1A1A",
          50: "#2C2C2C",
          100: "#262626",
          200: "#1F1F1F",
          300: "#1A1A1A",
          400: "#141414",
          500: "#0F0F0F",
          600: "#090909",
          700: "#040404",
          800: "#000000",
          900: "#000000"
        },
        gray: {
          50: "#F9FAFB",
          100: "#F3F4F6",
          200: "#E5E7EB",
          300: "#D1D5DB",
          400: "#9CA3AF",
          500: "#6B7280",
          600: "#4B5563",
          700: "#374151",
          800: "#1F2937",
          900: "#111827"
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"]
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-dark': 'linear-gradient(to bottom, rgb(17, 24, 39), rgb(31, 41, 55))'
      }
    },
  },
  plugins: [],
};

export default config;
