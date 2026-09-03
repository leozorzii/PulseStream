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
      /* Sem border/rounded próprios: quem usa passa a superfície via
         className (a receita ILHA do SiteHeader). Duas fontes de borda saem
         as duas no HTML, e o twMerge não resolve rounded-lg vs rounded-full
         de forma óbvia para quem lê depois. */
      className={cn("flex items-center", className)}
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
            "rounded-full px-2.5 py-1 text-xs tabular-nums transition-colors",
            /* O selecionado era bg-secondary: 1.23:1 contra --background e
               1.16:1 contra o antigo fundo do header — praticamente invisível,
               e só funcionava porque a pessoa inferia pela posição. A distinção
               foi para a COR DO RÓTULO, onde há contraste de sobra:
               text-primary mede 5.72:1. O preenchimento vira reforço, não o
               sinal. (aria-pressed já cobria a tecnologia assistiva.) */
            valor === p.valor
              ? "bg-primary/15 font-medium text-primary"
              : "text-foreground/60 hover:text-foreground"
          )}
        >
          {p.rotulo}
        </button>
      ))}
    </div>
  )
}
