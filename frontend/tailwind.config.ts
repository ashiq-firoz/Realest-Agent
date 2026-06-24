import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        "on-error-container": "#93000a",
        "on-primary-fixed": "#281801",
        "on-tertiary-fixed-variant": "#3e4c16",
        "on-background": "#1b1c1c",
        "inverse-surface": "#303030",
        "surface-tint": "#725a39",
        "surface-container-highest": "#e4e2e1",
        "tertiary": "#56642b",
        "outline": "#7f766a",
        "on-tertiary-container": "#414e18",
        "on-secondary-fixed-variant": "#484828",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#afc07d",
        "on-surface-variant": "#4d453c",
        "surface-dim": "#dcd9d9",
        "secondary-fixed": "#e6e5b9",
        "on-surface": "#1b1c1c",
        "on-secondary-container": "#666643",
        "secondary-container": "#e6e5b9",
        "surface-container-high": "#eae8e7",
        "secondary": "#60603e",
        "background": "#fbf9f8",
        "primary": "#725a39",
        "on-primary-fixed-variant": "#584324",
        "surface-container": "#f0eded",
        "inverse-on-surface": "#f3f0f0",
        "surface-bright": "#fbf9f8",
        "surface-container-lowest": "#ffffff",
        "error-container": "#ffdad6",
        "primary-container": "#d2b48c",
        "outline-variant": "#d1c5b8",
        "primary-fixed": "#feddb3",
        "secondary-fixed-dim": "#cac99f",
        "on-primary": "#ffffff",
        "primary-fixed-dim": "#e1c299",
        "tertiary-fixed-dim": "#bdce89",
        "error": "#ba1a1a",
        "surface": "#fbf9f8",
        "on-error": "#ffffff",
        "on-secondary-fixed": "#1d1d03",
        "inverse-primary": "#e1c299",
        "surface-container-low": "#f6f3f2",
        "on-tertiary-fixed": "#161f00",
        "on-secondary": "#ffffff",
        "on-primary-container": "#5b4526",
        "tertiary-fixed": "#d9eaa3",
        "surface-variant": "#e4e2e1",
        // Keep standard shadcn vars mapped to custom theme where applicable or keep them for compatibility
        border: "#d1c5b8", // outline-variant
        input: "#dcd9d9", // surface-dim
        ring: "#725a39", // primary
        foreground: "#1b1c1c", // on-background
        destructive: {
          DEFAULT: "#ba1a1a", // error
          foreground: "#ffffff", // on-error
        },
        muted: {
          DEFAULT: "#eae8e7", // surface-container-high
          foreground: "#4d453c", // on-surface-variant
        },
        accent: {
          DEFAULT: "#afc07d", // tertiary-container
          foreground: "#414e18", // on-tertiary-container
        },
        popover: {
          DEFAULT: "#fbf9f8", // surface
          foreground: "#1b1c1c", // on-surface
        },
        card: {
          DEFAULT: "#fbf9f8", // surface
          foreground: "#1b1c1c", // on-surface
        },
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "12px",
        "full": "9999px",
        // Shadcn compatibility
        md: "calc(0.5rem - 2px)",
        sm: "calc(0.5rem - 4px)",
      },
      spacing: {
        "md": "16px",
        "gutter": "16px",
        "lg": "24px",
        "container-margin": "20px",
        "unit": "4px",
        "xl": "32px",
        "sm": "8px",
        "xs": "4px"
      },
      fontFamily: {
        "label-sm": ["var(--font-jakarta)"],
        "headline-lg": ["var(--font-newsreader)"],
        "body-md": ["var(--font-jakarta)"],
        "label-md": ["var(--font-jakarta)"],
        "headline-lg-mobile": ["var(--font-newsreader)"],
        "display-lg": ["var(--font-newsreader)"],
        "body-lg": ["var(--font-jakarta)"],
        "headline-md": ["var(--font-newsreader)"],
        sans: ["var(--font-jakarta)"],
        serif: ["var(--font-newsreader)"],
      },
      fontSize: {
        "label-sm": ["12px", { lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "700" }],
        "headline-lg": ["32px", { lineHeight: "40px", fontWeight: "500" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "label-md": ["14px", { lineHeight: "20px", letterSpacing: "0.01em", fontWeight: "600" }],
        "headline-lg-mobile": ["28px", { lineHeight: "36px", fontWeight: "500" }],
        "display-lg": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "600" }],
        "body-lg": ["18px", { lineHeight: "28px", fontWeight: "400" }],
        "headline-md": ["24px", { lineHeight: "32px", fontWeight: "500" }]
      }
    },
  },
  plugins: [animate],
};

export default config;