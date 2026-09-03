/** Seções da página única. A ordem aqui é a ordem no documento — o scroll-spy
 *  depende disso para saber qual está visível. */
export type ItemNav = { id: string; titulo: string }

export const SECOES: ItemNav[] = [
  { id: "visao-geral", titulo: "Visão geral" },
  { id: "tendencia", titulo: "Tendência" },
  { id: "fontes", titulo: "Fontes" },
  { id: "posts", titulo: "Posts" },
]

export const IDS_SECOES = SECOES.map((s) => s.id)

/** Altura do cabeçalho fixo, em px. Vive aqui e não numa classe do Tailwind
 *  porque três lugares precisam do mesmo número: a altura do próprio header,
 *  o scroll-padding-top (para a âncora não ficar embaixo dele) e o cálculo de
 *  altura do herói. */
export const ALTURA_CABECALHO = 64
