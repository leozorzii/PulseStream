import * as React from "react"
import { motion, useReducedMotion } from "framer-motion"
import { Link } from "react-router-dom"
import {
  AtSign,
  Camera,
  Hash,
  MessageSquare,
  Newspaper,
  Video,
  type LucideIcon,
} from "lucide-react"

import { SentimentMeter } from "@/components/SentimentMeter"
import { Button } from "@/components/ui/button"
import { haQuantoTempo } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { Fonte, Plataforma } from "@/lib/mock"

/* O lucide removeu os ícones de marca (Instagram, Twitter, YouTube) por
 * questão de marca registrada, então usamos genéricos que descrevem o MEIO
 * em vez da empresa — o que envelhece melhor de qualquer forma. */
const PLATAFORMA: Record<Plataforma, { rotulo: string; icone: LucideIcon }> = {
  NEWS: { rotulo: "Portal de Notícias", icone: Newspaper },
  YOUTUBE: { rotulo: "YouTube", icone: Video },
  TWITTER: { rotulo: "Twitter / X", icone: AtSign },
  INSTAGRAM: { rotulo: "Instagram", icone: Camera },
  REDDIT: { rotulo: "Reddit", icone: MessageSquare },
}

export function SourcesTable({
  fontes,
  onColetar,
  coletandoId,
}: {
  fontes: Fonte[]
  onColetar?: (fonte: Fonte) => void
  coletandoId?: number | null
}) {
  const semMovimento = useReducedMotion()

  // Le o relogio UMA vez, na montagem, em vez de a cada render: Date.now()
  // durante o render e impuro e o resultado muda a cada re-render sem motivo.
  const [agora] = React.useState(() => Date.now())

  return (
    <div className="rounded-xl border bg-card">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <h3 className="font-display text-lg font-semibold uppercase tracking-wide">
          Fontes monitoradas
        </h3>
        <p className="text-sm text-muted-foreground">
          {fontes.filter((f) => f.is_active).length} ativas ·{" "}
          {fontes.filter((f) => !f.is_active).length} pausadas
        </p>
      </div>

      {/* Cabeçalho só no desktop: em telas pequenas cada linha vira um cartão
          empilhado, e uma grade de 12 colunas ali seria ilegível. */}
      <div className="hidden grid-cols-12 gap-4 px-5 py-2 text-xs font-medium uppercase tracking-wider text-muted-foreground lg:grid">
        <div className="col-span-3">Fonte</div>
        <div className="col-span-2">Plataforma</div>
        <div className="col-span-2">Última coleta</div>
        <div className="col-span-3">Sentimento</div>
        <div className="col-span-2 text-right">Ação</div>
      </div>

      <motion.ul
        className="divide-y divide-border"
        initial={semMovimento ? false : "oculto"}
        animate="visivel"
        variants={{ visivel: { transition: { staggerChildren: 0.05 } } }}
      >
        {fontes.map((fonte) => (
          <LinhaFonte
            key={fonte.id}
            fonte={fonte}
            onColetar={onColetar}
            coletando={coletandoId === fonte.id}
            semMovimento={!!semMovimento}
            agora={agora}
          />
        ))}
      </motion.ul>
    </div>
  )
}

function LinhaFonte({
  fonte,
  onColetar,
  coletando,
  semMovimento,
  agora,
}: {
  fonte: Fonte
  onColetar?: (fonte: Fonte) => void
  coletando: boolean
  semMovimento: boolean
  agora: number
}) {
  const { rotulo, icone: IconePlataforma } = PLATAFORMA[fonte.plataform]

  // Sem feed_url não há o que coletar por RSS. Hoje o backend só descobre isso
  // DEPOIS do clique, devolvendo 400 — ver issue #28. Com o campo exposto, o
  // botão já nasce desabilitado com o motivo, que é a affordance correta.
  const podeColetar = Boolean(fonte.feed_url) && fonte.is_active
  const motivoBloqueio = !fonte.is_active
    ? "Fonte pausada"
    : !fonte.feed_url
      ? "Sem feed_url configurada"
      : undefined

  return (
    <motion.li
      variants={{
        oculto: { opacity: 0, x: -12 },
        visivel: {
          opacity: 1,
          x: 0,
          transition: semMovimento
            ? { duration: 0 }
            : { type: "spring", stiffness: 400, damping: 30 },
        },
      }}
      className={cn(
        "grid grid-cols-1 gap-3 px-5 py-4 transition-colors hover:bg-muted/40 lg:grid-cols-12 lg:items-center lg:gap-4",
        !fonte.is_active && "opacity-60"
      )}
    >
      <div className="lg:col-span-3">
        <Link
          to={`/sources/${fonte.id}`}
          className="font-medium hover:text-primary hover:underline"
        >
          {fonte.name}
        </Link>
        <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
          <Hash className="h-3 w-3" aria-hidden />
          <span className="truncate">{fonte.external_id}</span>
        </p>
      </div>

      <div className="flex items-center gap-2 text-sm text-muted-foreground lg:col-span-2">
        <IconePlataforma className="h-4 w-4 shrink-0" aria-hidden />
        <span className="truncate">{rotulo}</span>
      </div>

      <div className="text-sm lg:col-span-2">
        <UltimaColeta iso={fonte.last_collected_at} agora={agora} />
        {fonte.pending_count > 0 && (
          <p className="text-xs text-muted-foreground">
            {fonte.pending_count} na fila
          </p>
        )}
      </div>

      <div className="flex items-center gap-3 lg:col-span-3">
        <SentimentMeter distribuicao={fonte.sentiment} />
        <span className="text-xs tabular-nums text-muted-foreground">
          {fonte.post_count > 0 ? `${fonte.post_count} posts` : "sem posts"}
        </span>
      </div>

      <div className="lg:col-span-2 lg:text-right">
        <Button
          size="sm"
          variant={podeColetar ? "secondary" : "ghost"}
          disabled={!podeColetar || coletando}
          onClick={() => onColetar?.(fonte)}
          title={motivoBloqueio}
        >
          {coletando ? "Coletando…" : "Coletar agora"}
        </Button>
        {motivoBloqueio && (
          <p className="mt-1 text-xs text-muted-foreground lg:text-right">
            {motivoBloqueio}
          </p>
        )}
      </div>
    </motion.li>
  )
}

/** Frescor importa mais que a data exata: "62% positivo" significa outra coisa
 *  se a última coleta foi há três semanas. */
function UltimaColeta({ iso, agora }: { iso: string | null; agora: number }) {
  if (!iso) return <span className="text-muted-foreground">Nunca coletada</span>

  const horas = (agora - new Date(iso).getTime()) / 36e5
  // Mais de dois dias sem coletar já é sinal: o número na tela pode estar
  // descrevendo um mundo que não existe mais.
  const velho = horas > 48
  const texto = haQuantoTempo(iso, agora)

  return (
    <span className={cn(velho ? "text-sentiment-negative" : "text-foreground")}>
      {texto}
    </span>
  )
}
