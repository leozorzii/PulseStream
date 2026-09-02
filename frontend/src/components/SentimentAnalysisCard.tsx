import * as React from "react"
import { motion, useReducedMotion } from "framer-motion"
import { Sparkles } from "lucide-react"

import { cn } from "@/lib/utils"
import {
  SENTIMENT,
  dominantSentiment,
  type SentimentSlice,
} from "@/lib/sentiment"

export interface SentimentAnalysisCardProps
  extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  /** Percentuais por sentimento. Mesmo formato de
   *  GET /api/analytics/summary/, só que já em lista e ordenado. */
  slices: SentimentSlice[]
}

const SentimentAnalysisCard = React.forwardRef<
  HTMLDivElement,
  SentimentAnalysisCardProps
>(({ title, slices, className, ...props }, ref) => {
  const semMovimento = useReducedMotion()

  const total = React.useMemo(
    () => slices.reduce((acc, s) => acc + s.value, 0),
    [slices]
  )

  // O sentimento do cabeçalho é DERIVADO dos dados. No componente original
  // essa cor era text-green-500 fixo, então uma fonte 70% negativa ainda
  // aparecia verde — o número dizia uma coisa e a cor dizia outra.
  const dominante = dominantSentiment(slices)
  const meta = SENTIMENT[dominante]

  // A API devolve {} para fonte sem análise, então vazio é caso real e não
  // paranoia defensiva.
  const vazio = slices.length === 0 || total === 0

  return (
    <div
      ref={ref}
      className={cn(
        // sem max-w aqui de proposito: quem decide largura e o grid da
        // pagina, nao o componente. O max-w-md do original brigava com o grid.
        "w-full rounded-xl border bg-card p-6 text-card-foreground shadow-sm",
        className
      )}
      aria-labelledby="sentiment-card-title"
      role="region"
      {...props}
    >
      <div className="mb-4 flex items-center justify-between">
        <h3
          id="sentiment-card-title"
          className="text-lg font-semibold text-card-foreground"
        >
          {title}
        </h3>

        {!vazio && (
          <div
            className={cn(
              "flex items-center gap-2 text-sm font-medium",
              meta.textClass
            )}
          >
            <Sparkles aria-hidden />
            <span>{meta.label}</span>
          </div>
        )}
      </div>

      {vazio ? (
        <p className="text-sm text-muted-foreground">
          Nenhuma análise ainda para esta fonte.
        </p>
      ) : (
        <>
          <div
            className="relative mb-4 flex h-4 w-full overflow-hidden rounded-full bg-muted"
            role="progressbar"
            aria-label={`Distribuição de sentimento: ${slices
              .map((s) => `${SENTIMENT[s.tone].label} ${percentual(s.value, total)}%`)
              .join(", ")}`}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            {slices.map((slice, index) => (
              <motion.div
                key={slice.tone}
                className={cn("h-full", SENTIMENT[slice.tone].barClass)}
                initial={semMovimento ? false : { width: "0%" }}
                animate={{ width: `${(slice.value / total) * 100}%` }}
                transition={{
                  duration: semMovimento ? 0 : 0.8,
                  ease: "easeInOut",
                  delay: semMovimento ? 0 : index * 0.1,
                }}
                style={{
                  // separa as fatias com a cor do próprio card, dando a
                  // impressão de um vão em vez de uma linha desenhada
                  borderRight:
                    index < slices.length - 1
                      ? "2px solid hsl(var(--card))"
                      : "none",
                }}
              />
            ))}
          </div>

          <div className="flex flex-wrap items-center justify-start gap-x-6 gap-y-2 text-sm text-muted-foreground">
            {slices.map((slice) => {
              const { label, textClass, icon: Icon } = SENTIMENT[slice.tone]
              return (
                <div key={slice.tone} className="flex items-center gap-2">
                  <Icon className={cn("h-4 w-4", textClass)} aria-hidden />
                  <span>{label}</span>
                  <span className="tabular-nums text-foreground">
                    {percentual(slice.value, total)}%
                  </span>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
})

SentimentAnalysisCard.displayName = "SentimentAnalysisCard"

/** A API devolve float cru (66.66666666666666); uma casa basta na tela. */
function percentual(valor: number, total: number): string {
  return ((valor / total) * 100).toFixed(1)
}

export { SentimentAnalysisCard }
