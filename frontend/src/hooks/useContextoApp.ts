import { useOutletContext } from "react-router-dom"

import type { EstadoColeta } from "@/components/StatusPill"
import type { Periodo } from "@/lib/periodo"

/** Estado que o RootLayout possui e as páginas consomem: período global,
 *  estado do pipeline e a ação de coletar. Vive num arquivo próprio para o
 *  RootLayout exportar SÓ o componente — arquivo que exporta componente e
 *  helper junto desliga o fast refresh do Vite. */
export type ContextoApp = {
  periodo: Periodo
  estadoColeta: EstadoColeta
  coletandoId: number | null
  coletar: (id: number | null) => void
}

/** useOutletContext sem tipo devolve unknown, e cada página faria seu cast. */
export function useContextoApp() {
  return useOutletContext<ContextoApp>()
}
