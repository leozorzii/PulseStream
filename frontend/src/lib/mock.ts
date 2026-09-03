import type { SentimentLabel } from "@/lib/sentiment"

/*
 * DADOS DE EXEMPLO
 * ----------------
 * Cada tipo aqui espelha a forma EXATA do endpoint que ainda não existe, e o
 * comentário cita a issue que vai criá-lo. A intenção é que ligar na API real
 * seja trocar a origem do dado, não redesenhar componente.
 *
 * Quando a issue correspondente for fechada, o tipo migra para services/ e o
 * mock some — os componentes não mudam.
 */

// ---------------------------------------------------------------- overview
/** GET /api/analytics/overview/ — issue #29 */
export type Overview = {
  total_posts: number
  analyzed_posts: number
  pending_posts: number
  active_sources: number
  sentiment: Record<SentimentLabel, number>
  avg_polarity: number
  last_collected_at: string
  trend: { avg_polarity_previous_period: number; window_days: number }
}

export const MOCK_OVERVIEW: Overview = {
  total_posts: 1284,
  analyzed_posts: 1247,
  pending_posts: 37,
  active_sources: 4,
  sentiment: { POS: 58.3, NEU: 27.1, NEG: 14.6 },
  avg_polarity: 0.28,
  last_collected_at: "2026-09-02T16:45:00-03:00",
  trend: { avg_polarity_previous_period: 0.21, window_days: 7 },
}

// -------------------------------------------------------------- timeseries
/** GET /api/analytics/timeseries/ — issue #24.
 *  Contagens e não percentuais: percentual esconde volume, e um dia com 2
 *  posts não pode parecer igual a um dia com 200. */
export type TimeseriesPoint = {
  date: string
  POS: number
  NEU: number
  NEG: number
  avg_polarity: number
}

/** 30 dias determinísticos. Sem Math.random: dado que muda a cada render
 *  impede comparar screenshots e esconde bug de re-render. */
export const MOCK_TIMESERIES: TimeseriesPoint[] = Array.from(
  { length: 30 },
  (_, i) => {
    const onda = Math.sin(i / 4.5)
    const deriva = i / 30

    // Uma crise entre os dias 12 e 18: volume dispara e o negativo domina.
    // Sem um evento assim a série fica lisa e o gráfico vira um bloco sólido —
    // que não demonstra nada. Dado de exemplo tem que exercitar o componente.
    const crise = i >= 12 && i <= 18 ? Math.sin(((i - 12) / 6) * Math.PI) : 0

    const POS = Math.round(14 + onda * 6 + deriva * 10 - crise * 9)
    const NEG = Math.round(9 - onda * 4 + (1 - deriva) * 5 + crise * 38)
    const NEU = Math.round(8 + Math.cos(i / 3) * 3 + crise * 6)
    const total = POS + NEU + NEG
    const data = new Date(2026, 7, 4 + i)
    return {
      date: data.toISOString().slice(0, 10),
      POS,
      NEU,
      NEG,
      avg_polarity: Number(((POS - NEG) / total).toFixed(3)),
    }
  }
)

// ------------------------------------------------------------------ fontes
/** GET /api/sources/ com os campos da issue #28 (feed_url, last_collected_at,
 *  contagens) e com fontes inativas incluídas. */
export type Plataforma = "NEWS" | "YOUTUBE" | "TWITTER" | "INSTAGRAM" | "REDDIT"

export type Fonte = {
  id: number
  name: string
  plataform: Plataforma
  external_id: string
  feed_url: string | null
  is_active: boolean
  last_collected_at: string | null
  post_count: number
  pending_count: number
  sentiment: Record<SentimentLabel, number>
}

export const MOCK_FONTES: Fonte[] = [
  {
    id: 4,
    name: "G1 Tecnologia",
    plataform: "NEWS",
    external_id: "g1_tecnologia",
    feed_url: "https://g1.globo.com/rss/g1/tecnologia/",
    is_active: true,
    last_collected_at: "2026-09-02T16:45:00-03:00",
    post_count: 412,
    pending_count: 0,
    sentiment: { POS: 62.5, NEU: 25.0, NEG: 12.5 },
  },
  {
    id: 7,
    name: "G1 Economia",
    plataform: "NEWS",
    external_id: "g1_economia",
    feed_url: "https://g1.globo.com/rss/g1/economia/",
    is_active: true,
    last_collected_at: "2026-09-02T16:45:00-03:00",
    post_count: 388,
    pending_count: 37,
    sentiment: { POS: 31.2, NEU: 44.1, NEG: 24.7 },
  },
  {
    id: 9,
    name: "Canal de Reclamações",
    plataform: "YOUTUBE",
    external_id: "UC_reclamacoes",
    // Sem feed_url: fonte de YouTube não é coletável por RSS. É o caso que
    // hoje só falha DEPOIS do clique, com 400 — ver issue #28.
    feed_url: null,
    is_active: true,
    last_collected_at: "2026-08-28T09:12:00-03:00",
    post_count: 296,
    pending_count: 0,
    sentiment: { POS: 14.3, NEU: 21.4, NEG: 64.3 },
  },
  {
    id: 11,
    name: "r/brasil",
    plataform: "REDDIT",
    external_id: "r_brasil",
    feed_url: "https://www.reddit.com/r/brasil/.rss",
    is_active: true,
    last_collected_at: null,
    post_count: 0,
    pending_count: 0,
    // Fonte criada e nunca coletada: a API devolve {} nesse caso — issue #31.
    sentiment: { POS: 0, NEU: 0, NEG: 0 },
  },
  {
    id: 13,
    name: "Portal Antigo",
    plataform: "NEWS",
    external_id: "portal_antigo",
    feed_url: "https://exemplo.com/feed",
    is_active: false,
    last_collected_at: "2026-06-14T08:00:00-03:00",
    post_count: 188,
    pending_count: 0,
    sentiment: { POS: 44.0, NEU: 38.0, NEG: 18.0 },
  },
]

// -------------------------------------------------------------------- feed
/** GET /api/posts/ — issue #26. Post junto do sentimento dele. */
export type PostAnalisado = {
  id: number
  text_content: string
  published_at: string
  source: { id: number; name: string; plataform: Plataforma }
  sentiment: {
    label: SentimentLabel
    polarity_score: number
    extracted_keywords: string[]
  }
}

export const MOCK_POSTS: PostAnalisado[] = [
  {
    id: 981,
    text_content:
      "Atualização chegou rápido e resolveu o travamento que eu reclamei semana passada. Suporte respondeu em minutos.",
    published_at: "2026-09-02T15:12:00-03:00",
    source: { id: 4, name: "G1 Tecnologia", plataform: "NEWS" },
    sentiment: { label: "POS", polarity_score: 0.82, extracted_keywords: ["suporte", "atualização"] },
  },
  {
    id: 977,
    text_content:
      "Preço subiu de novo e a entrega atrasou três dias. Terceira vez no mês que isso acontece.",
    published_at: "2026-09-02T14:03:00-03:00",
    source: { id: 7, name: "G1 Economia", plataform: "NEWS" },
    sentiment: { label: "NEG", polarity_score: -0.74, extracted_keywords: ["preço", "entrega", "atraso"] },
  },
  {
    id: 970,
    text_content:
      "O relatório saiu hoje. Números vieram dentro do esperado, sem grande novidade em relação ao trimestre anterior.",
    published_at: "2026-09-02T11:40:00-03:00",
    source: { id: 7, name: "G1 Economia", plataform: "NEWS" },
    sentiment: { label: "NEU", polarity_score: 0.02, extracted_keywords: ["relatório", "trimestre"] },
  },
  {
    id: 964,
    text_content:
      "Péssimo atendimento. Fiquei duas horas na fila do chat e ninguém resolveu absolutamente nada.",
    published_at: "2026-09-02T09:21:00-03:00",
    source: { id: 9, name: "Canal de Reclamações", plataform: "YOUTUBE" },
    sentiment: { label: "NEG", polarity_score: -0.91, extracted_keywords: ["atendimento", "fila"] },
  },
  {
    id: 958,
    text_content:
      "Interface nova ficou ótima, muito mais rápida que a anterior. Só senti falta do modo escuro.",
    published_at: "2026-09-01T18:55:00-03:00",
    source: { id: 4, name: "G1 Tecnologia", plataform: "NEWS" },
    sentiment: { label: "POS", polarity_score: 0.61, extracted_keywords: ["interface", "rápida"] },
  },
  /* Os três abaixo são mais antigos DE PROPÓSITO: com todos os posts na mesma
   * semana, trocar o filtro de período não mudava a lista e dava a impressão
   * de que o feed ignorava o controle. Dado de exemplo tem que exercitar o
   * comportamento, senão esconde justamente o que precisa ser conferido. */
  {
    id: 902,
    text_content:
      "Sistema fora do ar desde ontem e nenhuma posição oficial. Prejuízo acumulando.",
    published_at: "2026-08-21T10:30:00-03:00",
    source: { id: 9, name: "Canal de Reclamações", plataform: "YOUTUBE" },
    sentiment: { label: "NEG", polarity_score: -0.88, extracted_keywords: ["sistema", "prejuízo"] },
  },
  {
    id: 874,
    text_content:
      "Migração concluída sem downtime. Equipe de infraestrutura fez um trabalho impecável.",
    published_at: "2026-08-16T14:10:00-03:00",
    source: { id: 4, name: "G1 Tecnologia", plataform: "NEWS" },
    sentiment: { label: "POS", polarity_score: 0.77, extracted_keywords: ["migração", "equipe"] },
  },
  {
    id: 841,
    text_content:
      "Balanço trimestral divulgado. Receita estável, sem variação relevante frente ao período anterior.",
    published_at: "2026-08-09T09:00:00-03:00",
    source: { id: 7, name: "G1 Economia", plataform: "NEWS" },
    sentiment: { label: "NEU", polarity_score: -0.04, extracted_keywords: ["balanço", "receita"] },
  },
]

// ------------------------------------------------------------- palavras-chave
/** GET /api/analytics/keywords/ — issue #27. */
export type Keyword = { term: string; count: number; dominant_label: SentimentLabel }

export const MOCK_KEYWORDS: Keyword[] = [
  { term: "atendimento", count: 34, dominant_label: "NEG" },
  { term: "preço", count: 31, dominant_label: "NEG" },
  { term: "entrega", count: 27, dominant_label: "NEU" },
  { term: "suporte", count: 24, dominant_label: "POS" },
  { term: "interface", count: 21, dominant_label: "POS" },
  { term: "atraso", count: 18, dominant_label: "NEG" },
  { term: "relatório", count: 15, dominant_label: "NEU" },
  { term: "atualização", count: 12, dominant_label: "POS" },
]

// ---------------------------------------------------------------- histograma
/** Distribuição de polarity_score em 10 baldes sobre [-1, +1] — issue #25.
 *  É o que separa "opinião polarizada" de "opinião morna": os dois casos
 *  produzem o mesmo percentual de NEU hoje. */
export const MOCK_HISTOGRAMA: number[] = [8, 14, 22, 31, 47, 68, 91, 74, 41, 19]
