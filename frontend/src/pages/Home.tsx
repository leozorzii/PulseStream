import * as React from "react"

import { Hero } from "@/components/Hero"
import { KpiCard } from "@/components/KpiCard"
import { PostsFeed } from "@/components/PostsFeed"
import { SourcesTable } from "@/components/SourcesTable"
import { StatusPill, type EstadoColeta } from "@/components/StatusPill"
import { KeywordsList } from "@/components/charts/KeywordsChart"
import {
  SentimentLegend,
  SentimentTrendChart,
} from "@/components/charts/SentimentTrendChart"
import { SENTIMENT } from "@/lib/sentiment"
import {
  MOCK_FONTES,
  MOCK_KEYWORDS,
  MOCK_OVERVIEW,
  MOCK_POSTS,
  MOCK_TIMESERIES,
  type Fonte,
} from "@/lib/mock"

export default function Home() {
  const [coletandoId, setColetandoId] = React.useState<number | null>(null)
  const [estado, setEstado] = React.useState<EstadoColeta>("ocioso")

  /* Simula o ciclo real: o endpoint de trigger coleta de forma síncrona e
   * devolve, e só então a task do Celery analisa em background. Por isso são
   * dois estados e não um — é o que o usuário de fato observa. */
  const coletar = (fonte: Fonte) => {
    setColetandoId(fonte.id)
    setEstado("coletando")
    window.setTimeout(() => setEstado("analisando"), 1400)
    window.setTimeout(() => {
      setEstado("ocioso")
      setColetandoId(null)
    }, 3200)
  }

  const { sentiment, avg_polarity, trend } = MOCK_OVERVIEW
  const deltaPolaridade = avg_polarity - trend.avg_polarity_previous_period

  // Sparklines: percentual positivo e polaridade média por dia, derivados da
  // mesma série do gráfico grande — nunca de um mock separado, ou os números
  // divergem entre si na mesma tela.
  const seriePositivo = MOCK_TIMESERIES.map(
    (d) => Math.round((d.POS / (d.POS + d.NEU + d.NEG)) * 100)
  )
  const seriePolaridade = MOCK_TIMESERIES.map((d) => d.avg_polarity)

  return (
    <>
      <Hero />

      <section id="analises" className="container mx-auto scroll-mt-8 px-4 pb-24">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="font-display text-3xl font-semibold uppercase tracking-wide">
              Análises
            </h2>
            <p className="mt-1 text-sm text-foreground/70">
              Dados de exemplo — as issues [DEPENDENCIA BACKEND] listam os
              endpoints que faltam para ligar isto na API.
            </p>
          </div>

          <StatusPill
            estado={estado}
            detalhe={
              estado === "ocioso"
                ? `${MOCK_OVERVIEW.pending_posts} na fila`
                : undefined
            }
          />
        </header>

        {/* KPIs ------------------------------------------------------------ */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label="Sentimento positivo"
            valor={`${sentiment.POS.toFixed(1)}%`}
            delta={2.1}
            sufixoDelta=" pts"
            serie={seriePositivo}
            corSerie={SENTIMENT.POS.cor}
            linhas={[
              { label: "Neutro", valor: `${sentiment.NEU.toFixed(1)}%` },
              {
                label: "Negativo",
                valor: `${sentiment.NEG.toFixed(1)}%`,
                delta: -1.2,
                // subir o negativo é RUIM: a cor do delta não pode sair
                // do sinal do número
                maiorEhMelhor: false,
              },
            ]}
          />

          <KpiCard
            label="Polaridade média"
            valor={avg_polarity.toFixed(2)}
            delta={Number((deltaPolaridade * 100).toFixed(1))}
            sufixoDelta=" pts"
            serie={seriePolaridade}
            linhas={[
              {
                label: `Período anterior (${trend.window_days}d)`,
                valor: trend.avg_polarity_previous_period.toFixed(2),
              },
            ]}
          />

          <KpiCard
            label="Posts analisados"
            valor={MOCK_OVERVIEW.analyzed_posts.toLocaleString("pt-BR")}
            linhas={[
              {
                label: "Total coletado",
                valor: MOCK_OVERVIEW.total_posts.toLocaleString("pt-BR"),
              },
              {
                label: "Na fila",
                valor: MOCK_OVERVIEW.pending_posts.toLocaleString("pt-BR"),
              },
            ]}
          />

          <KpiCard
            label="Fontes ativas"
            valor={String(MOCK_OVERVIEW.active_sources)}
            linhas={[
              {
                label: "Última coleta",
                valor: new Date(MOCK_OVERVIEW.last_collected_at).toLocaleString("pt-BR", {
                  day: "2-digit",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                }),
              },
              {
                label: "Pausadas",
                valor: String(MOCK_FONTES.filter((f) => !f.is_active).length),
              },
            ]}
          />
        </div>

        {/* Tendência ------------------------------------------------------- */}
        <div className="mt-6 rounded-xl border bg-card p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-display text-lg font-semibold uppercase tracking-wide">
                Sentimento ao longo do tempo
              </h3>
              <p className="text-sm text-muted-foreground">
                Posts por dia, últimos 30 dias
              </p>
            </div>
            <SentimentLegend />
          </div>

          <SentimentTrendChart dados={MOCK_TIMESERIES} />
        </div>

        {/* Fontes ---------------------------------------------------------- */}
        <div className="mt-6">
          <SourcesTable
            fontes={MOCK_FONTES}
            onColetar={coletar}
            coletandoId={coletandoId}
          />
        </div>

        {/* Evidência + palavras -------------------------------------------- */}
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <PostsFeed posts={MOCK_POSTS} />
          </div>

          <div className="rounded-xl border bg-card p-5">
            <h3 className="font-display text-lg font-semibold uppercase tracking-wide">
              Assuntos
            </h3>
            <p className="mb-4 text-sm text-muted-foreground">
              Termos mais frequentes e o humor dominante de cada um
            </p>
            <KeywordsList dados={MOCK_KEYWORDS} />
          </div>
        </div>
      </section>
    </>
  )
}
