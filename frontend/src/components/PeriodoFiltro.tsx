import { cn } from "@/lib/utils"
import { PERIODOS, type Periodo } from "@/lib/periodo"

/** Filtro global de período. Fica no cabeçalho porque governa TODA a tela que
 *  tem eixo de tempo — gráfico, sparklines dos KPIs e feed de posts. Os dois
 *  blocos sem dimensão temporal (histograma e assuntos) dizem isso na legenda,
 *  porque controle que rege parte da tela sem avisar é pior que nenhum. */
export function PeriodoFiltro({
  valor,
  onChange,
  className,
}: {
  valor: Periodo
  onChange: (p: Periodo) => void
  className?: string
}) {
  return (
    <div
      className={cn("flex items-center rounded-lg border border-border p-0.5", className)}
      role="group"
      aria-label="Período de análise"
    >
      {PERIODOS.map((p) => (
        <button
          key={p.valor}
          type="button"
          onClick={() => onChange(p.valor)}
          aria-pressed={valor === p.valor}
          className={cn(
            "rounded-md px-2.5 py-1 text-xs tabular-nums transition-colors",
            valor === p.valor
              ? "bg-secondary text-secondary-foreground"
              : "text-foreground/60 hover:text-foreground"
          )}
        >
          {p.rotulo}
        </button>
      ))}
    </div>
  )
}
