import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts"

import { SENTIMENT } from "@/lib/sentiment"
import type { Keyword } from "@/lib/mock"

/*
 * Palavras-chave — barras horizontais, pintadas pelo sentimento dominante.
 *
 * Horizontal e não vertical porque os rótulos são palavras: na vertical elas
 * viram texto rotacionado, que é uma das piores decisões possíveis para
 * leitura. Na horizontal cabem alinhadas à esquerda e leem-se normalmente.
 *
 * A cor aqui responde "com que humor as pessoas falam disto", que é o que
 * transforma uma nuvem de frequência em achado: "preço" aparecer 31 vezes é
 * ruído; "preço, majoritariamente negativo" é informação.
 */
export function KeywordsChart({ dados }: { dados: Keyword[] }) {
  const altura = Math.max(200, dados.length * 34)

  return (
    <div style={{ height: altura }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={dados}
          layout="vertical"
          margin={{ top: 0, right: 32, bottom: 0, left: 0 }}
          barCategoryGap={8}
        >
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="term"
            width={104}
            stroke="hsl(var(--muted-foreground))"
            tickLine={false}
            axisLine={false}
            fontSize={13}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]} isAnimationActive={false}>
            {dados.map((d) => (
              <Cell key={d.term} fill={SENTIMENT[d.dominant_label].cor} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** A contagem sai como rótulo direto ao lado da barra, não como eixo: são
 *  poucas séries e o número exato importa mais que a escala. */
export function KeywordsList({ dados }: { dados: Keyword[] }) {
  const maior = Math.max(...dados.map((d) => d.count))

  return (
    <ul className="space-y-2.5">
      {dados.map((d) => {
        const { label, cor, textClass, icon: Icone } = SENTIMENT[d.dominant_label]
        return (
          <li key={d.term} className="flex items-center gap-3 text-sm">
            <Icone className={`h-4 w-4 shrink-0 ${textClass}`} aria-hidden />
            <span className="w-28 shrink-0 truncate">{d.term}</span>
            <span className="h-2.5 flex-1 overflow-hidden rounded-full bg-muted">
              <span
                className="block h-full rounded-full"
                style={{ width: `${(d.count / maior) * 100}%`, backgroundColor: cor }}
              />
            </span>
            <span className="w-8 shrink-0 text-right tabular-nums text-muted-foreground">
              {d.count}
            </span>
            <span className="sr-only">{label}</span>
          </li>
        )
      })}
    </ul>
  )
}
