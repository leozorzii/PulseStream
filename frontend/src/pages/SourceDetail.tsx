import * as React from "react"
import { ArrowLeft } from "lucide-react"
import { Link, useParams } from "react-router-dom"

import { KpiCard } from "@/components/KpiCard"
import { PostsFeed } from "@/components/PostsFeed"
import { SentimentAnalysisCard } from "@/components/SentimentAnalysisCard"
import { KeywordsList } from "@/components/charts/KeywordsChart"
import {
  SentimentLegend,
  SentimentTrendChart,
} from "@/components/charts/SentimentTrendChart"
import { useContextoApp } from "@/hooks/useContextoApp"
import { Button } from "@/components/ui/button"
import { haQuantoTempo } from "@/lib/format"
import { agregarPeriodo, fatiarSerie } from "@/lib/periodo"
import { PLATAFORMA } from "@/lib/plataforma"
import { SENTIMENT, SENTIMENT_ORDER, type SentimentSlice } from "@/lib/sentiment"
import { MOCK_FONTES, MOCK_KEYWORDS, MOCK_POSTS, MOCK_TIMESERIES } from "@/lib/mock"

export default function SourceDetail() {
  const { id } = useParams<{ id: string }>()
  const { periodo, coletandoId, coletar } = useContextoApp()

  // Lê o relógio UMA vez, na montagem: Date.now() durante o render é impuro e
  // o "há N h" mudaria a cada re-render sem motivo.
  const [agora] = React.useState(() => Date.now())

  const fonte = MOCK_FONTES.find((f) => String(f.id) === id)

  if (!fonte) return <NaoEncontrada id={id} />

  const { icone: Icone, rotulo } = PLATAFORMA[fonte.plataform]
  const serie = fatiarSerie(MOCK_TIMESERIES, periodo)
  const { percentuais, polaridadeMedia, total } = agregarPeriodo(serie)

  const posts = MOCK_POSTS.filter((p) => p.source.id === fonte.id)
  const fatias: SentimentSlice[] = SENTIMENT_ORDER.map((tone) => ({
    tone,
    value: fonte.sentiment[tone],
  })).filter((f) => f.value > 0)

  const podeColetar = Boolean(fonte.feed_url) && fonte.is_active
  const motivoBloqueio = !fonte.is_active
    ? "Fonte pausada"
    : !fonte.feed_url
      ? "Sem feed_url configurada — não é coletável por RSS"
      : undefined

  // Fonte criada e nunca coletada: a API devolve {} nesse caso (issue #31), e
  // é estado real, não defensiva.
  const semDados = fonte.post_count === 0

  return (
    <div className="container mx-auto px-4 py-10">
      <Link
        to="/#fontes"
        className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Todas as fontes
      </Link>

      <header className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-semibold uppercase tracking-wide">
            {fonte.name}
          </h1>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-foreground/70">
            <span className="flex items-center gap-1.5">
              <Icone className="h-4 w-4" aria-hidden />
              {rotulo}
            </span>
            <span>·</span>
            <span className="font-mono text-xs">{fonte.external_id}</span>
            <span>·</span>
            <span>
              {fonte.last_collected_at
                ? `coletada ${haQuantoTempo(fonte.last_collected_at, agora)}`
                : "nunca coletada"}
            </span>
            {!fonte.is_active && (
              <>
                <span>·</span>
                <span className="text-sentiment-negative">pausada</span>
              </>
            )}
          </p>
        </div>

        <div className="text-right">
          <Button
            onClick={() => coletar(fonte.id)}
            disabled={!podeColetar || coletandoId === fonte.id}
            title={motivoBloqueio}
          >
            {coletandoId === fonte.id ? "Coletando…" : "Coletar agora"}
          </Button>
          {motivoBloqueio && (
            <p className="mt-1.5 max-w-[16rem] text-xs text-foreground/60">
              {motivoBloqueio}
            </p>
          )}
        </div>
      </header>

      {semDados ? (
        <div className="mt-8 rounded-xl border bg-card p-10 text-center">
          <p className="text-lg">Esta fonte ainda não tem posts.</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {podeColetar
              ? "Dispare uma coleta para começar a acumular análises."
              : motivoBloqueio}
          </p>
        </div>
      ) : (
        <>
          <div className="mt-8 grid gap-4 lg:grid-cols-3">
            {/* O SentimentAnalysisCard existia sem uso desde que a tabela
                passou a usar o SentimentMeter nas linhas. Esta é a tela dele:
                o resumo em destaque de UMA fonte. */}
            <SentimentAnalysisCard title="Distribuição" slices={fatias} />

            <KpiCard
              label="Polaridade média"
              valor={polaridadeMedia.toFixed(2)}
              serie={serie.map((d) => d.avg_polarity)}
              linhas={[
                { label: "Posts no período", valor: total.toLocaleString("pt-BR") },
                { label: "Total da fonte", valor: fonte.post_count.toLocaleString("pt-BR") },
              ]}
            />

            <KpiCard
              label="Sentimento positivo"
              valor={`${percentuais.POS.toFixed(1)}%`}
              serie={serie.map((d) => Math.round((d.POS / (d.POS + d.NEU + d.NEG)) * 100))}
              corSerie={SENTIMENT.POS.cor}
              linhas={[
                { label: "Na fila", valor: String(fonte.pending_count) },
                { label: "Negativo", valor: `${percentuais.NEG.toFixed(1)}%`, maiorEhMelhor: false },
              ]}
            />
          </div>

          <div className="mt-6 rounded-xl border bg-card p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-display text-lg font-semibold uppercase tracking-wide">
                  Tendência
                </h2>
                <p className="text-sm text-muted-foreground">
                  Posts por dia, últimos {periodo} dias
                </p>
              </div>
              <SentimentLegend />
            </div>
            <SentimentTrendChart dados={serie} />
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <PostsFeed posts={posts} />
            </div>

            <div className="rounded-xl border bg-card p-5">
              <h2 className="font-display text-lg font-semibold uppercase tracking-wide">
                Assuntos
              </h2>
              <p className="mb-4 text-sm text-muted-foreground">
                Termos mais frequentes desta fonte
              </p>
              <KeywordsList dados={MOCK_KEYWORDS.slice(0, 5)} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function NaoEncontrada({ id }: { id?: string }) {
  return (
    <div className="container mx-auto px-4 py-24 text-center">
      <h1 className="font-display text-3xl font-semibold uppercase tracking-wide">
        Fonte não encontrada
      </h1>
      <p className="mt-2 text-foreground/70">
        Nenhuma fonte com o id <span className="font-mono">{id}</span>.
      </p>
      <Button asChild className="mt-6">
        <Link to="/#fontes">Ver todas as fontes</Link>
      </Button>
    </div>
  )
}
