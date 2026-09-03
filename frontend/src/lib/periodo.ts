import type { PostAnalisado, TimeseriesPoint } from "@/lib/mock"

export type Periodo = 7 | 30 | 90

export const PERIODOS: { valor: Periodo; rotulo: string }[] = [
  { valor: 7, rotulo: "7 d" },
  { valor: 30, rotulo: "30 d" },
  { valor: 90, rotulo: "90 d" },
]

/** Últimos N pontos da série. O mock tem 30, então 90 devolve tudo — que é
 *  exatamente o que a API vai fazer quando a issue #24 aceitar ?days=. */
export function fatiarSerie(
  serie: TimeseriesPoint[],
  periodo: Periodo
): TimeseriesPoint[] {
  return serie.slice(Math.max(0, serie.length - periodo))
}

/** Recorta os posts pelo mesmo período. Sem isto o filtro governaria só os
 *  gráficos, e controle que rege metade da tela é pior que controle nenhum. */
export function fatiarPosts(
  posts: PostAnalisado[],
  serieFatiada: TimeseriesPoint[]
): PostAnalisado[] {
  if (serieFatiada.length === 0) return []
  const inicio = new Date(`${serieFatiada[0].date}T00:00:00`).getTime()
  return posts.filter((p) => new Date(p.published_at).getTime() >= inicio)
}

/** Agrega uma fatia da série no mesmo formato do endpoint de overview
 *  (issue #29), para os KPIs responderem ao período em vez de ficarem
 *  congelados nos números estáticos do mock. */
export function agregarPeriodo(serie: TimeseriesPoint[]) {
  const totais = serie.reduce(
    (acc, d) => ({ POS: acc.POS + d.POS, NEU: acc.NEU + d.NEU, NEG: acc.NEG + d.NEG }),
    { POS: 0, NEU: 0, NEG: 0 }
  )
  const total = totais.POS + totais.NEU + totais.NEG || 1

  return {
    totais,
    total,
    percentuais: {
      POS: (totais.POS / total) * 100,
      NEU: (totais.NEU / total) * 100,
      NEG: (totais.NEG / total) * 100,
    },
    polaridadeMedia:
      serie.reduce((acc, d) => acc + d.avg_polarity, 0) / (serie.length || 1),
  }
}
