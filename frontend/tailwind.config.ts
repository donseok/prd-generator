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
          50: "#EEF2FF",
          100: "#E0E7FF",
          200: "#C7D2FE",
          300: "#A5B4FC",
          400: "#818CF8",
          500: "#6366F1",
          600: "#4F46E5",
          700: "#4338CA",
          800: "#3730A3",
          900: "#312E81",
          950: "#1E1B4B",
        },
        accent: {
          50: "#ECFEFF",
          100: "#CFFAFE",
          200: "#A5F3FC",
          300: "#67E8F9",
          400: "#22D3EE",
          500: "#06B6D4",
          600: "#0891B2",
          700: "#0E7490",
          800: "#155E75",
          900: "#164E63",
          950: "#083344",
        },
      },
      fontFamily: {
        sans: ["Pretendard Variable", "Pretendard", "system-ui", "sans-serif"],
      },
      animation: {
        shimmer: "shimmer 2s ease-in-out infinite",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "gradient-shift": "gradient-shift 6s ease infinite",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "glow-pulse": {
          "0%, 100%": {
            boxShadow:
              "0 0 8px rgba(99, 102, 241, 0.15), 0 0 24px rgba(99, 102, 241, 0.05)",
          },
          "50%": {
            boxShadow:
              "0 0 16px rgba(99, 102, 241, 0.3), 0 0 48px rgba(139, 92, 246, 0.1)",
          },
        },
        "gradient-shift": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
      boxShadow: {
        glow: "0 0 16px rgba(99, 102, 241, 0.2), 0 0 48px rgba(139, 92, 246, 0.08)",
        "glow-lg":
          "0 0 24px rgba(99, 102, 241, 0.25), 0 0 64px rgba(139, 92, 246, 0.12)",
        "card-premium":
          "0 0 0 1px rgba(15, 15, 30, 0.03), 0 1px 2px rgba(15, 15, 30, 0.04), 0 4px 12px rgba(15, 15, 30, 0.03)",
        "card-premium-hover":
          "0 0 0 1px rgba(99, 102, 241, 0.06), 0 4px 8px rgba(15, 15, 30, 0.06), 0 12px 32px rgba(15, 15, 30, 0.08)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-primary": "linear-gradient(135deg, #6366F1, #8B5CF6)",
        "gradient-cyan": "linear-gradient(135deg, #06B6D4, #22D3EE)",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
