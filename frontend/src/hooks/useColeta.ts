import * as React from "react"

import type { EstadoColeta } from "@/components/StatusPill"

/** Simula o ciclo real do pipeline: o endpoint de trigger coleta de forma
 *  síncrona e responde, e só então a task do Celery analisa em background.
 *  São dois estados porque é o que a pessoa de fato observa.
 *
 *  Os timers são limpos no unmount — sem isso, sair da página no meio de uma
 *  coleta agendaria setState em componente desmontado. */
export function useColeta() {
  const [estado, setEstado] = React.useState<EstadoColeta>("ocioso")
  const [coletandoId, setColetandoId] = React.useState<number | null>(null)
  const timers = React.useRef<number[]>([])

  React.useEffect(() => {
    const atuais = timers.current
    return () => atuais.forEach((t) => window.clearTimeout(t))
  }, [])

  const coletar = React.useCallback((id: number | null) => {
    timers.current.forEach((t) => window.clearTimeout(t))
    timers.current = []

    setColetandoId(id)
    setEstado("coletando")

    timers.current.push(window.setTimeout(() => setEstado("analisando"), 1400))
    timers.current.push(
      window.setTimeout(() => {
        setEstado("ocioso")
        setColetandoId(null)
      }, 3200)
    )
  }, [])

  return { estado, coletandoId, coletar }
}
