import * as React from "react"
import { Outlet, useLocation } from "react-router-dom"

import { BeamsBackground } from "@/components/BeamsBackground"
import { SiteHeader } from "@/components/layout/SiteHeader"
import { useColeta } from "@/hooks/useColeta"
import { useScrollSpy } from "@/hooks/useScrollSpy"
import { ALTURA_CABECALHO, IDS_SECOES } from "@/lib/nav"
import { MOCK_FONTES, MOCK_OVERVIEW } from "@/lib/mock"
import type { Periodo } from "@/lib/periodo"

/** Casca do app: fundo + cabeçalho fixo. Sem bg-background aqui de propósito
 *  — o body já pinta o fundo e essa cor propaga para o canvas, atrás do -z-10
 *  do padrão. Um fundo opaco nesta div ficaria NA FRENTE e o apagaria. */
export default function RootLayout() {
  const [periodo, setPeriodo] = React.useState<Periodo>(30)
  const { estado, coletandoId, coletar } = useColeta()
  const secaoAtiva = useScrollSpy(IDS_SECOES, ALTURA_CABECALHO)
  const { hash, pathname } = useLocation()

  /* O React Router NÃO rola até o hash depois de navegação client-side: ir de
     /sources/4 para /#fontes trocava a URL e deixava a página no topo. Este
     efeito faz o que o navegador faria numa navegação de documento. */
  React.useEffect(() => {
    if (!hash) return
    const alvo = document.getElementById(hash.slice(1))
    if (!alvo) return
    // rAF porque o elemento pode ainda não ter sido pintado no mesmo tick
    const id = requestAnimationFrame(() => alvo.scrollIntoView({ block: "start" }))
    return () => cancelAnimationFrame(id)
  }, [hash, pathname])

  return (
    <div className="min-h-dvh">
      <BeamsBackground />

      <SiteHeader
        // Fora da home não existe seção nenhuma para marcar, e o scroll-spy
        // cairia no padrão (a primeira) — o indicador apontaria "Visão geral"
        // numa página que não a tem.
        secaoAtiva={pathname === "/" ? secaoAtiva : null}
        fontes={MOCK_FONTES}
        periodo={periodo}
        onPeriodo={setPeriodo}
        estadoColeta={estado}
        detalheColeta={
          estado === "ocioso" ? `${MOCK_OVERVIEW.pending_posts} na fila` : undefined
        }
        onColetarTudo={() => coletar(null)}
      />

      <Outlet context={{ periodo, estadoColeta: estado, coletandoId, coletar }} />
    </div>
  )
}
