import { Area, AreaChart, ResponsiveContainer } from "recharts"
import { ArrowDown, ArrowUp, Minus } from "lucide-react"

import { cn } from "@/lib/utils"

export type KpiLinha = { label: string; valor: string; delta?: number; maiorEhMelhor?: boolean }

export interface KpiCardProps {
  label: string
  valor: string
  delta?: number
  /** Se subir é bom. Em sentimento isso NÃO é universal: mais posts negativos
   *  subindo é ruim, então a cor do delta não pode sair do sinal do número. */
  maiorEhMelhor?: boolean
  sufixoDelta?: string
  linhas?: KpiLinha[]
  /** Série do sparkline. Sem eixo e sem tooltip de propósito: é contexto de
   *  forma, não um gráfico para ler valor — quem lê valor é o número grande. */
  serie?: number[]
  corSerie?: string
  className?: string
}

export function KpiCard({
  label,
  valor,
  delta,
  maiorEhMelhor = true,
  sufixoDelta = "%",
  linhas,
  serie,
  corSerie = "hsl(var(--primary))",
  className,
}: KpiCardProps) {
  const dadosSerie = serie?.map((v, i) => ({ i, v }))
  const idGradiente = `kpi-${label.replace(/\W/g, "")}`

  return (
    <div
      className={cn(
        "flex flex-col rounded-xl border bg-card p-5 text-card-foreground",
        className
      )}
    >
      <p className="text-sm text-muted-foreground">{label}</p>

      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-3xl font-semibold tabular-nums">{valor}</span>
        {delta !== undefined && (
          <DeltaBadge delta={delta} maiorEhMelhor={maiorEhMelhor} sufixo={sufixoDelta} />
        )}
      </div>

      {linhas && linhas.length > 0 && (
        <dl className="mt-4 space-y-2">
          {linhas.map((linha) => (
            <div key={linha.label} className="flex items-center gap-2 text-sm">
              <dt className="text-muted-foreground">{linha.label}</dt>
              <dd className="ml-auto flex items-center gap-2">
                <span className="tabular-nums font-medium">{linha.valor}</span>
                {linha.delta !== undefined && (
                  <DeltaBadge
                    delta={linha.delta}
                    maiorEhMelhor={linha.maiorEhMelhor ?? true}
                    sufixo={sufixoDelta}
                    discreto
                  />
                )}
              </dd>
            </div>
          ))}
        </dl>
      )}

      {dadosSerie && (
        <div className="-mx-1 mt-4 h-16" aria-hidden>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dadosSerie} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id={idGradiente} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={corSerie} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={corSerie} stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="v"
                stroke={corSerie}
                strokeWidth={2}
                fill={`url(#${idGradiente})`}
                dot={false}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

/** Delta com SETA, não só cor. Cor sozinha não é codificação acessível, e a
 *  seta ainda diz a direção para quem não distingue verde de vermelho. */
function DeltaBadge({
  delta,
  maiorEhMelhor,
  sufixo,
  discreto = false,
}: {
  delta: number
  maiorEhMelhor: boolean
  sufixo: string
  discreto?: boolean
}) {
  const subiu = delta > 0
  const parado = delta === 0
  const bom = parado ? null : subiu === maiorEhMelhor

  const Icone = parado ? Minus : subiu ? ArrowUp : ArrowDown
  const cor = parado
    ? "text-muted-foreground"
    : bom
      ? "text-sentiment-positive"
      : "text-sentiment-negative"

  const sinal = subiu ? "+" : ""
  const rotulo = `${sinal}${delta.toFixed(1)}${sufixo}`

  if (discreto) {
    return (
      <span className={cn("flex items-center gap-0.5 text-xs tabular-nums", cor)}>
        <Icone className="h-3 w-3" aria-hidden />
        {rotulo}
      </span>
    )
  }

  return (
    <span
      className={cn(
        "flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-xs font-medium tabular-nums",
        parado ? "bg-muted" : bom ? "bg-sentiment-positive/15" : "bg-sentiment-negative/15",
        cor
      )}
    >
      <Icone className="h-3 w-3" aria-hidden />
      {rotulo}
    </span>
  )
}
