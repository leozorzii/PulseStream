/** @type {import('tailwindcss').Config} */

/*
 * DESIGN TOKENS — convencao shadcn/ui
 * -----------------------------------
 * Componente nunca nomeia cor crua (bg-zinc-900, text-red-500). Nomeia um
 * PAPEL: bg-background, bg-card, text-muted-foreground, border-border. Esse e
 * o mesmo vocabulario que os componentes do shadcn/ui e do 21st.dev usam,
 * entao da pra colar um componente sem editar nada e ele herda esta paleta.
 *
 * Os valores vivem como triplas HSL em src/index.css ("200 20% 6%") e sao
 * consumidos aqui como hsl(var(--x)). Guardar a tripla em vez da cor pronta
 * e o que deixa o Tailwind emitir hsl(var(--card) / 0.5) para bg-card/50.
 *
 * Papeis:
 *   background / foreground      a pagina em si
 *   card / popover               superficies elevadas
 *   primary                      o teal da marca: acoes, links, foco
 *   secondary / muted / accent   preenchimentos cada vez mais discretos.
 *                                ATENCAO: accent aqui e superficie de HOVER,
 *                                NAO a cor da marca. A marca e primary.
 *   destructive                  erros e acoes perigosas
 *   border / input / ring        linhas e contorno de foco
 *   sentiment.{positive,neutral,negative}
 *                                vocabulario do dominio, espelha os labels
 *                                POS / NEU / NEG que a API devolve
 */

export default {
  darkMode: "class",
  // ts,tsx e obrigatorio: sem isso o app renderiza SEM ESTILO NENHUM e o
  // build passa em silencio, porque o Tailwind so nao acha as classes
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        sentiment: {
          positive: "hsl(var(--sentiment-positive))",
          neutral: "hsl(var(--sentiment-neutral))",
          negative: "hsl(var(--sentiment-negative))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
