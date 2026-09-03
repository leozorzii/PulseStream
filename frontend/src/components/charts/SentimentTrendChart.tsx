import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { ChartTooltip } from "@/components/charts/ChartTooltip"
import { formatarData } from "@/lib/format"
import { SENTIMENT, SENTIMENT_ORDER } from "@/lib/sentiment"
import type { TimeseriesPoint } from "@/lib/mock"

/*
 * Sentimento ao longo do tempo — área empilhada, contagem por dia.
 *
 * Empilhada e não linhas sobrepostas porque a pergunta é dupla: "qual o
 * volume total" (a altura da pilha) e "como se reparte" (as faixas). Três
 * linhas soltas respondem só a segunda e ainda se cruzam.
 *
 * A ordem das faixas é fixa (POS, NEU, NEG) — sem isso as camadas trocariam
 * de lugar entre requisições e a leitura de tendência seria impossível.
 */
export function SentimentTrendChart({ dados }: { dados: TimeseriesPoint[] }) {
  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={dados} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
          {/* grade recessiva: orienta sem competir com os dados */}
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="hsl(var(--border))"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            tickFormatter={formatarData}
            stroke="hsl(var(--muted-foreground))"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            minTickGap={24}
          />
          <YAxis
            stroke="hsl(var(--muted-foreground))"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={44}
          />
          <Tooltip
            content={<ChartTooltip />}
            cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1 }}
          />

          {SENTIMENT_ORDER.map((tone) => (
            <Area
              key={tone}
              type="monotone"
              dataKey={tone}
              stackId="sentimento"
              stroke={SENTIMENT[tone].cor}
              fill={SENTIMENT[tone].cor}
              fillOpacity={0.85}
              // 2px da cor da superfície entre as faixas: separa as camadas
              // sem desenhar uma linha, que é o que as diretrizes pedem para
              // marcas empilhadas
              strokeWidth={2}
              name={SENTIMENT[tone].label}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Legenda com ícone + rótulo. Fica fora do gráfico porque é a codificação
 *  secundária que torna a paleta legível para daltônicos — não é decoração. */
export function SentimentLegend() {
  return (
    <ul className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
      {SENTIMENT_ORDER.map((tone) => {
        const { label, textClass, icon: Icone } = SENTIMENT[tone]
        return (
          <li key={tone} className="flex items-center gap-2">
            <Icone className={`h-4 w-4 ${textClass}`} aria-hidden />
            <span className="text-muted-foreground">{label}</span>
          </li>
        )
      })}
    </ul>
  )
}
