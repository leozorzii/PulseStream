/** @type {import('tailwindcss').Config} */

/*
 * SEMANTIC COLOR TOKENS
 * ---------------------
 * Never use raw Tailwind colors (bg-gray-100, text-red-600) in components.
 * Use the semantic tokens below instead, so the whole UI can be re-themed
 * from one place and a dark theme is a variable swap, not a refactor.
 *
 * Available tokens:
 *
 *   Surfaces & text
 *     bg-background      page background
 *     bg-surface         cards, panels, anything raised above the page
 *     border-border      dividers and outlines
 *     text-text-primary  headings and body copy
 *     text-text-muted    secondary/supporting copy
 *     bg-accent          primary actions, links, focus rings
 *
 *   Sentiment (the domain's core vocabulary)
 *     sentiment-positive   maps to the "POS" label
 *     sentiment-neutral    maps to the "NEU" label
 *     sentiment-negative   maps to the "NEG" label
 *
 * Each token works with every Tailwind utility that takes a color
 * (bg-, text-, border-, ring-, fill-, stroke-) and supports opacity
 * modifiers, e.g. bg-sentiment-positive/10 for a soft badge background.
 *
 * The actual values live as CSS variables in src/index.css, defined once
 * for light and once under .dark — see that file to change the palette.
 *
 * Note: colors are stored as space-separated RGB channels ("22 163 74"),
 * not hex. That is what makes the <alpha-value> placeholder work; a hex
 * value there would break every opacity modifier.
 */

// helper so every token supports opacity modifiers
const token = (name) => `rgb(var(${name}) / <alpha-value>)`

export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class", // toggle by putting .dark on <html>
  theme: {
    extend: {
      colors: {
        background: token("--color-background"),
        surface: token("--color-surface"),
        border: token("--color-border"),
        "text-primary": token("--color-text-primary"),
        "text-muted": token("--color-text-muted"),
        accent: token("--color-accent"),
        sentiment: {
          positive: token("--color-sentiment-positive"),
          neutral: token("--color-sentiment-neutral"),
          negative: token("--color-sentiment-negative"),
        },
      },
    },
  },
  plugins: [],
}
