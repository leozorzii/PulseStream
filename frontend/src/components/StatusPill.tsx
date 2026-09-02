import { useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"

export type EstadoColeta = "ocioso" | "coletando" | "analisando" | "erro"

const ESTADOS: Record<EstadoColeta, { rotulo: string; cor: string; pulsa: boolean }> = {
  ocioso: { rotulo: "Ocioso", cor: "bg-muted-foreground", pulsa: false },
  coletando: { rotulo: "Coletando…", cor: "bg-primary", pulsa: true },
  analisando: { rotulo: "Analisando…", cor: "bg-primary", pulsa: true },
  erro: { rotulo: "Falhou", cor: "bg-sentiment-negative", pulsa: false },
}

/*
 * Indicador do pipeline. É o que dá sensação de sistema vivo: a coleta é uma
 * ação real, com Celery atrás, e o estado muda sozinho enquanto o worker
 * processa.
 *
 * Ponto pulsante em vez do orb em canvas da referência: a informação é
 * binária (está rodando ou não), e um canvas animado permanente custa frame
 * a frame — o mesmo tipo de gasto que já derrubou a landing uma vez. Se o orb
 * for desejado depois, entra aqui sem mudar nada de quem usa.
 */
export function StatusPill({
  estado,
  detalhe,
  className,
}: {
  estado: EstadoColeta
  detalhe?: string
  className?: string
}) {
  const semMovimento = useReducedMotion()
  const { rotulo, cor, pulsa } = ESTADOS[estado]

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2.5 rounded-full border border-border bg-card/80 py-1.5 pl-2.5 pr-4",
        className
      )}
      // status: leitor de tela anuncia a mudança sem roubar o foco
      role="status"
    >
      <span className="relative flex h-2.5 w-2.5">
        {pulsa && !semMovimento && (
          <span className={cn("absolute inline-flex h-full w-full animate-ping rounded-full opacity-60", cor)} />
        )}
        <span className={cn("relative inline-flex h-2.5 w-2.5 rounded-full", cor)} />
      </span>

      <span className="text-sm text-muted-foreground">
        {rotulo}
        {detalhe && <span className="ml-1.5 text-foreground">{detalhe}</span>}
      </span>
    </div>
  )
}
