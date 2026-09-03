import * as React from "react"

import { Hero } from "@/components/Hero"
import { KpiCard } from "@/components/KpiCard"
import { PostsFeed } from "@/components/PostsFeed"
import { SourcesTable } from "@/components/SourcesTable"
import { KeywordsList } from "@/components/charts/KeywordsChart"
import { PolarityHistogram } from "@/components/charts/PolarityHistogram"
import {
  SentimentLegend,
  SentimentTrendChart,
} from "@/components/charts/SentimentTrendChart"
import { useContextoApp } from "@/hooks/useContextoApp"
import { haQuantoTempo } from "@/lib/format"
import { SENTIMENT } from "@/lib/sentiment"
import { agregarPeriodo, fatiarPosts, fatiarSerie } from "@/lib/periodo"
import {
  MOCK_FONTES,
  MOCK_HISTOGRAMA,
  MOCK_KEYWORDS,
  MOCK_OVERVIEW,
  MOCK_POSTS,
  MOCK_TIMESERIES,
} from "@/lib/mock"

export default function Home() {
  const { periodo, coletandoId, coletar } = useContextoApp()

  /* Lê o relógio UMA vez, na montagem — mesma regra do SourceDetail. Este
     componente re-renderiza a cada troca de período, e Date.now() no render
     faria o "há N h" mudar junto sem motivo. */
  const [agora] = React.useState(() => Date.now())
  const fontesAtivas = MOCK_FONTES.filter((f) => f.is_active).length

  /* Tudo que tem eixo de tempo é DERIVADO da série fatiada, e não dos campos
   * estáticos do MOCK_OVERVIEW. É o que torna o filtro do cabeçalho honesto:
   * mexer nele muda gráfico, sparklines, KPIs e feed juntos. */
  const serie = fatiarSerie(MOCK_TIMESERIES, periodo)
  const { percentuais, polaridadeMedia, total } = agregarPeriodo(serie)
  const posts = fatiarPosts(MOCK_POSTS, serie)

  const metadeAnterior = serie.slice(0, Math.floor(serie.length / 2))
  const metadeRecente = serie.slice(Math.floor(serie.length / 2))
  const deltaPos =
    agregarPeriodo(metadeRecente).percentuais.POS -
    agregarPeriodo(metadeAnterior).percentuais.POS
  const deltaPolaridade =
    agregarPeriodo(metadeRecente).polaridadeMedia -
    agregarPeriodo(metadeAnterior).polaridadeMedia

  const seriePositivo = serie.map((d) =>
    Math.round((d.POS / (d.POS + d.NEU + d.NEG)) * 100)
  )
  const seriePolaridade = serie.map((d) => d.avg_polarity)

  return (
    <>
      <Hero
        selo={{
          primario: `${fontesAtivas} ${fontesAtivas === 1 ? "fonte ativa" : "fontes ativas"}`,
          secundario: `última coleta ${haQuantoTempo(MOCK_OVERVIEW.last_collected_at, agora)}`,
          href: "visao-geral",
        }}
      />

      {/* Visão geral ------------------------------------------------------ */}
      <section id="visao-geral" className="container mx-auto px-4 pt-10">
        <header className="mb-6">
          <h2 className="font-display text-3xl font-semibold uppercase tracking-wide">
            Visão geral
          </h2>
          <p className="mt-1 text-sm text-foreground/70">
            Últimos {periodo} dias · dados de exemplo — as issues [DEPENDENCIA
            BACKEND] listam os endpoints que faltam.
          </p>
        </header>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label="Sentimento positivo"
            valor={`${percentuais.POS.toFixed(1)}%`}
            delta={Number(deltaPos.toFixed(1))}
            sufixoDelta=" pts"
            serie={seriePositivo}
            corSerie={SENTIMENT.POS.cor}
            linhas={[
              { label: "Neutro", valor: `${percentuais.NEU.toFixed(1)}%` },
              {
                label: "Negativo",
                valor: `${percentuais.NEG.toFixed(1)}%`,
                // subir o negativo é RUIM: a cor do delta não pode sair do
                // sinal do número
                maiorEhMelhor: false,
              },
            ]}
          />

          <KpiCard
            label="Polaridade média"
            valor={polaridadeMedia.toFixed(2)}
            delta={Number((deltaPolaridade * 100).toFixed(1))}
            sufixoDelta=" pts"
            serie={seriePolaridade}
            linhas={[
              { label: "Posts no período", valor: total.toLocaleString("pt-BR") },
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
      </section>

      {/* Tendência -------------------------------------------------------- */}
      <section id="tendencia" className="container mx-auto px-4 pt-10">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-xl border bg-card p-5 lg:col-span-2">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="font-display text-lg font-semibold uppercase tracking-wide">
                  Sentimento ao longo do tempo
                </h3>
                <p className="text-sm text-muted-foreground">
                  Posts por dia, últimos {periodo} dias
                </p>
              </div>
              <SentimentLegend />
            </div>

            <SentimentTrendChart dados={serie} />
          </div>

          <div className="rounded-xl border bg-card p-5">
            <h3 className="font-display text-lg font-semibold uppercase tracking-wide">
              Polarização
            </h3>
            {/* Este bloco NÃO responde ao filtro de período, e dizer isso é
                mais honesto que deixar o leitor supor que responde. */}
            <p className="mb-4 text-sm text-muted-foreground">
              Distribuição acumulada — não filtrada por período
            </p>
            <PolarityHistogram baldes={MOCK_HISTOGRAMA} />
          </div>
        </div>
      </section>

      {/* Fontes ----------------------------------------------------------- */}
      <section id="fontes" className="container mx-auto px-4 pt-10">
        <SourcesTable
          fontes={MOCK_FONTES}
          onColetar={(f) => coletar(f.id)}
          coletandoId={coletandoId}
        />
      </section>

      {/* Posts + assuntos -------------------------------------------------- */}
      <section id="posts" className="container mx-auto px-4 pb-24 pt-10">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <PostsFeed posts={posts} />
          </div>

          <div className="rounded-xl border bg-card p-5">
            <h3 className="font-display text-lg font-semibold uppercase tracking-wide">
              Assuntos
            </h3>
            <p className="mb-4 text-sm text-muted-foreground">
              Termos mais frequentes e o humor dominante — não filtrado por período
            </p>
            <KeywordsList dados={MOCK_KEYWORDS} />
          </div>
        </div>
      </section>
    </>
  )
}
