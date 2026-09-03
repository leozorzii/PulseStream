import { cn } from "@/lib/utils"
import { SENTIMENT, SENTIMENT_ORDER, type SentimentLabel } from "@/lib/sentiment"

/*
 * Medidor segmentado — a ideia das 10 barrinhas de CPU da referência, aplicada
 * a sentimento.
 *
 * Por que segmentado e não uma barra contínua: em linha de tabela o espaço é
 * pequeno, e segmentos discretos dão uma leitura de "quantos décimos" que o
 * olho conta rápido, sem precisar de eixo. A barra contínua exige comparar
 * comprimentos entre linhas, que é mais lento.
 *
 * A ordem é sempre POS, NEU, NEG — mesma do resto do app, para a posição
 * também carregar significado além da cor.
 */
export function SentimentMeter({
  distribuicao,
  segmentos = 10,
  className,
}: {
  distribuicao: Record<SentimentLabel, number>
  segmentos?: number
  className?: string
}) {
  const total = SENTIMENT_ORDER.reduce((acc, t) => acc + (distribuicao[t] ?? 0), 0)

  if (total === 0) {
    return (
      <div className={cn("flex items-center gap-1", className)} aria-label="Sem análises">
        {Array.from({ length: segmentos }).map((_, i) => (
          <span key={i} className="h-5 w-1.5 rounded-full bg-muted" />
        ))}
      </div>
    )
  }

  // Distribui os segmentos proporcionalmente. O arredondamento pode sobrar ou
  // faltar um; o resto vai para o tom dominante, senão o medidor não fecha.
  const brutos = SENTIMENT_ORDER.map((t) => ((distribuicao[t] ?? 0) / total) * segmentos)
  const cheios = brutos.map((v) => Math.floor(v))
  let sobra = segmentos - cheios.reduce((a, b) => a + b, 0)
  const ordemResto = brutos
    .map((v, i) => ({ i, resto: v - Math.floor(v) }))
    .sort((a, b) => b.resto - a.resto)
  for (const { i } of ordemResto) {
    if (sobra <= 0) break
    cheios[i] += 1
    sobra -= 1
  }

  const pintados: SentimentLabel[] = []
  SENTIMENT_ORDER.forEach((tone, i) => {
    for (let n = 0; n < cheios[i]; n++) pintados.push(tone)
  })

  const descricao = SENTIMENT_ORDER.map(
    (t) => `${SENTIMENT[t].label} ${(((distribuicao[t] ?? 0) / total) * 100).toFixed(0)}%`
  ).join(", ")

  return (
    <div className={cn("flex items-center gap-1", className)} role="img" aria-label={descricao}>
      {pintados.map((tone, i) => (
        <span
          key={i}
          className={cn("h-5 w-1.5 rounded-full", SENTIMENT[tone].barClass)}
        />
      ))}
    </div>
  )
}
