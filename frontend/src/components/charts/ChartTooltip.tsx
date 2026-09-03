import { formatarData } from "@/lib/format"
import { SENTIMENT, type SentimentLabel } from "@/lib/sentiment"

type Entrada = { dataKey?: string | number; value?: number | string; name?: string }

/*
 * Tooltip compartilhado por todos os gráficos.
 *
 * Dois pontos que as diretrizes de visualização tratam como não-negociáveis e
 * que é fácil errar aqui:
 *
 * 1. O TEXTO usa tokens de texto, nunca a cor da série. A cor identifica a
 *    marca (o quadradinho ao lado), não o número — número colorido sobre
 *    superfície escura perde contraste e o valor é o que precisa ser lido.
 * 2. Todo item traz ÍCONE e RÓTULO junto da cor. Verde e vermelho ficam a
 *    ΔE 6.4 sob deuteranopia, o que só é permitido com essa codificação
 *    secundária — sem ela ~8% dos homens não distinguem as séries.
 */
export function ChartTooltip({
  active,
  payload,
  label,
  sufixo = "",
}: {
  active?: boolean
  payload?: Entrada[]
  label?: string | number
  sufixo?: string
}) {
  if (!active || !payload?.length) return null

  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 shadow-lg">
      {label !== undefined && (
        <p className="mb-1.5 text-xs text-muted-foreground">{formatarData(String(label))}</p>
      )}

      <ul className="space-y-1">
        {payload.map((item) => {
          const chave = String(item.dataKey) as SentimentLabel
          const meta = SENTIMENT[chave]
          if (!meta) return null
          const Icone = meta.icon

          return (
            <li key={chave} className="flex items-center gap-2 text-sm">
              <Icone className={`h-3.5 w-3.5 ${meta.textClass}`} aria-hidden />
              <span className="text-muted-foreground">{meta.label}</span>
              <span className="ml-auto tabular-nums font-medium text-popover-foreground">
                {item.value}
                {sufixo}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
