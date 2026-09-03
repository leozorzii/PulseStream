import { SENTIMENT } from "@/lib/sentiment"
import { cn } from "@/lib/utils"

/*
 * HISTOGRAMA DE POLARIDADE
 * ------------------------
 * Responde a pergunta que os três percentuais não respondem: a opinião está
 * POLARIZADA (massa nas duas pontas) ou MORNA (massa no centro)? Os dois casos
 * produzem o mesmo "50% neutro" no card de cima.
 *
 * Barras à mão, não recharts. O projeto já tomou essa decisão sozinho — o
 * KeywordsChart em recharts está sem uso enquanto o KeywordsList em divs é o
 * que está na tela. Dez barras num domínio simétrico não precisam de escala,
 * e o divisor do zero cai exatamente em left-1/2; uma ReferenceLine do
 * recharts sobre eixo de categoria desenharia no CENTRO do balde 5 (+0.1),
 * meio balde fora do lugar.
 *
 * POR QUE NÃO EXISTE BARRA NEUTRA
 * O classificador do backend rotula comparando contagens, não por banda morta:
 * empate produz polarity_score exatamente 0.0, e texto sem palavra carregada
 * também. Ou seja, NEU é um PICO em zero, sem largura — e com 10 baldes sobre
 * [-1, +1] o zero é BORDA entre o balde 4 e o 5, nunca interior de balde.
 * Pintar os centrais de neutro seria mentira: o balde 4 é [-0.2, 0.0),
 * inteiramente negativo. Por isso o zero vira linha tracejada rotulada, que é
 * onde a massa de NEU de fato mora.
 */

const BALDES = 10
const LARGURA_BALDE = 2 / BALDES // domínio [-1, +1]

export function PolarityHistogram({
  baldes,
  className,
}: {
  baldes: number[]
  className?: string
}) {
  const maior = Math.max(...baldes, 1)
  const total = baldes.reduce((a, b) => a + b, 0)

  return (
    <div className={cn("w-full", className)}>
      <div className="relative flex h-40 items-end gap-1">
        {baldes.map((valor, i) => {
          const inicio = -1 + i * LARGURA_BALDE
          const fim = inicio + LARGURA_BALDE
          // A cor segue o SINAL do balde. O balde inteiro está de um lado só
          // do zero, então não há ambiguidade a resolver.
          const negativo = fim <= 0
          const meta = negativo ? SENTIMENT.NEG : SENTIMENT.POS

          return (
            <div
              key={i}
              // h-full e items-end no wrapper: sem altura declarada aqui, o
              // height percentual da barra resolveria contra caixa de altura
              // zero e todas sairiam no mínimo de 2px.
              className="group flex h-full flex-1 items-end"
              // Rótulo por barra: são 10, e o valor exato importa mais que a
              // escala — por isso também não há eixo Y.
              title={`${inicio.toFixed(1)} a ${fim.toFixed(1)}: ${valor} posts`}
            >
              <div
                className="w-full rounded-t-sm transition-opacity group-hover:opacity-80"
                style={{
                  height: `${(valor / maior) * 100}%`,
                  // 2px mínimos: balde vazio precisa ler como "zero aqui" e
                  // não como "não existe balde aqui"
                  minHeight: 2,
                  backgroundColor: meta.cor,
                }}
              />
            </div>
          )
        })}

        {/* O zero. Tracejado e rotulado porque é onde a massa de NEU está —
            ela não tem barra própria, pelo motivo no comentário do topo. */}
        <div
          className="pointer-events-none absolute inset-y-0 left-1/2 w-px -translate-x-1/2 border-l border-dashed border-foreground/40"
          aria-hidden
        />
      </div>

      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <SENTIMENT.NEG.icon className={cn("h-3.5 w-3.5", SENTIMENT.NEG.textClass)} aria-hidden />
          −1,0
        </span>
        <span className="tabular-nums">neutro (0,0)</span>
        <span className="flex items-center gap-1.5">
          +1,0
          <SENTIMENT.POS.icon className={cn("h-3.5 w-3.5", SENTIMENT.POS.textClass)} aria-hidden />
        </span>
      </div>

      <p className="mt-3 text-xs text-muted-foreground">
        {total.toLocaleString("pt-BR")} posts por intensidade. Mede{" "}
        <span className="text-foreground">polarity_score</span>, enquanto os
        percentuais acima medem o <span className="text-foreground">rótulo</span> — são
        perguntas diferentes e não se espera que batam.
      </p>
    </div>
  )
}
