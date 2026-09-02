import { Frown, Meh, Smile, type LucideIcon } from "lucide-react"

/** Os códigos que a API emite — ver apps/stream_core/models.py. */
export type SentimentLabel = "POS" | "NEU" | "NEG"

type SentimentMeta = {
  label: string
  /** Strings de classe COMPLETAS e literais. Nunca monte como
   *  `bg-sentiment-${tone}`: o scanner do Tailwind é regex sobre o texto do
   *  arquivo, não avalia JavaScript. Uma classe montada em runtime não é
   *  gerada, e a barra renderiza transparente sem erro nenhum. */
  barClass: string
  textClass: string
  /** Cor pronta para SVG/Recharts, que não aceita classe do Tailwind — o
   *  atributo fill/stroke precisa de um valor CSS de verdade. Mesmo token
   *  das classes acima, então gráfico e badge nunca divergem. */
  cor: string
  icon: LucideIcon
}

export const SENTIMENT: Record<SentimentLabel, SentimentMeta> = {
  POS: {
    label: "Positivo",
    barClass: "bg-sentiment-positive",
    textClass: "text-sentiment-positive",
    cor: "hsl(var(--sentiment-positive))",
    icon: Smile,
  },
  NEU: {
    label: "Neutro",
    barClass: "bg-sentiment-neutral",
    textClass: "text-sentiment-neutral",
    cor: "hsl(var(--sentiment-neutral))",
    icon: Meh,
  },
  NEG: {
    label: "Negativo",
    barClass: "bg-sentiment-negative",
    textClass: "text-sentiment-negative",
    cor: "hsl(var(--sentiment-negative))",
    icon: Frown,
  },
}

/** Ordem de exibição fixa. A API devolve as chaves na ordem em que apareceram
 *  no banco, que não é estável — sem isto as fatias trocariam de lugar entre
 *  requisições. */
export const SENTIMENT_ORDER: SentimentLabel[] = ["POS", "NEU", "NEG"]

export type SentimentSlice = { tone: SentimentLabel; value: number }

/** Qual sentimento domina. Empate cai em NEU em vez de escolher um
 *  arbitrariamente — 50/50 entre positivo e negativo não é "positivo". */
export function dominantSentiment(slices: SentimentSlice[]): SentimentLabel {
  if (slices.length === 0) return "NEU"
  const max = Math.max(...slices.map((s) => s.value))
  const vencedores = slices.filter((s) => s.value === max)
  return vencedores.length === 1 ? vencedores[0].tone : "NEU"
}
