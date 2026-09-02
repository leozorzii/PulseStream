import { Hero } from "@/components/Hero"
import { SentimentAnalysisCard } from "@/components/SentimentAnalysisCard"
import type { SentimentSlice } from "@/lib/sentiment"

/*
 * MOCK. Espelha o formato de GET /api/analytics/summary/?source_id=<id>,
 * que devolve percentuais por label: {"POS": 62.5, "NEU": 25.0, "NEG": 12.5}.
 * Manter o mesmo formato agora faz a ligação com a API depois ser troca de
 * linha, não refatoração.
 */
const MOCK_POSITIVO: SentimentSlice[] = [
  { tone: "POS", value: 62.5 },
  { tone: "NEU", value: 25.0 },
  { tone: "NEG", value: 12.5 },
]

/* O segundo card existe como PROVA de que o bug do verde fixo morreu: aqui o
 * cabeçalho tem que sair vermelho, não verde. */
const MOCK_NEGATIVO: SentimentSlice[] = [
  { tone: "POS", value: 14.3 },
  { tone: "NEU", value: 21.4 },
  { tone: "NEG", value: 64.3 },
]

/* Fonte coletada mas ainda não analisada: a API devolve {} nesse caso. */
const MOCK_VAZIO: SentimentSlice[] = []

export default function Home() {
  return (
    <>
      <Hero />

      {/* scroll-mt dá respiro no destino da âncora #analises. */}
      <section id="analises" className="container mx-auto scroll-mt-8 px-4 pb-24">
        {/* h2, não h1: o h1 da página é o "PulseStream" do herói. */}
        <h2 className="font-display text-3xl font-semibold uppercase tracking-wide">Análises</h2>
        {/* foreground/70 e não muted-foreground: texto direto sobre o padrão. */}
        <p className="mt-1 text-sm text-foreground/70">
          Dados de exemplo — ainda não ligado à API.
        </p>

        <div className="mt-6 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          <SentimentAnalysisCard title="G1 Tecnologia" slices={MOCK_POSITIVO} />
          <SentimentAnalysisCard title="Canal de Reclamações" slices={MOCK_NEGATIVO} />
          <SentimentAnalysisCard title="Fonte recém-criada" slices={MOCK_VAZIO} />
        </div>
      </section>
    </>
  )
}
