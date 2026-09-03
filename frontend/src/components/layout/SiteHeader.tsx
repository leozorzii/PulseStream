import { Link } from "react-router-dom"

import { MobileNav } from "@/components/layout/MobileNav"
import { NavMenu } from "@/components/layout/NavMenu"
import { PeriodoFiltro } from "@/components/PeriodoFiltro"
import { StatusPill, type EstadoColeta } from "@/components/StatusPill"
import { Button } from "@/components/ui/button"
import { ALTURA_CABECALHO } from "@/lib/nav"
import type { Periodo } from "@/lib/periodo"
import type { Fonte } from "@/lib/mock"

/*
 * Cabeçalho fixo.
 *
 * bg-card/80 + backdrop-blur, nunca bg-background opaco: o padrão de cruzes
 * vive numa camada -z-10 e um fundo sólido aqui o apagaria. Como efeito
 * colateral útil, o backdrop-blur cria contexto de empilhamento — é por isso
 * que o z-50 do dropdown fica escopado aqui dentro e não briga com o resto.
 *
 * text-foreground/70 e não text-muted-foreground: esta superfície é
 * translúcida sobre o padrão, e muted-foreground ali mede 3.62:1.
 *
 * O StatusPill mora aqui, e não dentro da seção como antes: ele descreve o
 * ciclo do Celery, que continua rodando enquanto a pessoa rola a página. No
 * cabeçalho fixo ele fica sempre visível — que é o ponto de existir.
 */
export function SiteHeader({
  secaoAtiva,
  fontes,
  periodo,
  onPeriodo,
  estadoColeta,
  detalheColeta,
  onColetarTudo,
}: {
  secaoAtiva: string | null
  fontes: Fonte[]
  periodo: Periodo
  onPeriodo: (p: Periodo) => void
  estadoColeta: EstadoColeta
  detalheColeta?: string
  onColetarTudo?: () => void
}) {
  return (
    <header
      className="sticky top-0 z-40 border-b border-border bg-card/80 backdrop-blur-md"
      style={{ height: ALTURA_CABECALHO }}
    >
      <div className="relative mx-auto flex h-full max-w-[1400px] items-center gap-4 px-4">
        <Link
          to="/"
          className="shrink-0 font-display text-lg font-semibold uppercase tracking-wide"
        >
          Pulse<span className="text-primary">Stream</span>
        </Link>

        <div className="hidden md:block">
          <NavMenu secaoAtiva={secaoAtiva} fontes={fontes} />
        </div>

        <div className="ml-auto flex items-center gap-3">
          <PeriodoFiltro valor={periodo} onChange={onPeriodo} className="hidden sm:flex" />

          <StatusPill
            estado={estadoColeta}
            detalhe={detalheColeta}
            className="hidden lg:inline-flex"
          />

          <Button
            size="sm"
            onClick={onColetarTudo}
            disabled={estadoColeta !== "ocioso"}
            className="hidden sm:inline-flex"
          >
            Coletar tudo
          </Button>

          <MobileNav fontes={fontes} />
        </div>
      </div>
    </header>
  )
}
