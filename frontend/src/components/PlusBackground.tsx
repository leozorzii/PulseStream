import * as React from "react"

import { cn } from "@/lib/utils"

/*
 * Padrão de cruzes que fica atrás de todo o app.
 *
 * POR QUE MÁSCARA, E NÃO background-image
 * ---------------------------------------
 * O componente original do 21st.dev embute a cor DENTRO do data URI
 * (fill='%23fb3a5d'). Data URI é string opaca: o navegador nunca procura
 * var() lá dentro. Cravar o #1B99BB equivalente duplicaria o token --primary
 * e sairia de sincronia em silêncio no dia em que a paleta mudar.
 *
 * Aqui o SVG entra como MÁSCARA. Máscara de imagem usa mask-mode:
 * match-source, que para uma <image> resolve para `alpha` — só o canal alfa
 * é lido, o RGB é descartado. Por isso o fill lá dentro é preto fixo e
 * irrelevante, e por isso o fill-opacity='0.4' do original foi REMOVIDO:
 * ele multiplicaria com o alfa do gradiente e daria 0.16 efetivo.
 *
 * Quem pinta é o background-image de gradiente, que é CSS normal e resolve
 * var(). O gradiente faz DOIS trabalhos de uma vez: dá a cor da marca e dá o
 * fade radial. Por isso basta UMA máscara e UM elemento — sem
 * mask-composite: intersect, cujo equivalente antigo no WebKit usa outra
 * palavra-chave (source-in) e é o tipo de coisa que quebra só no Safari.
 *
 * Os prefixos -webkit- são escritos à mão de propósito: o autoprefixer é um
 * plugin PostCSS, roda sobre .css e NÃO enxerga style={{}} de React.
 */

/** Ladrilho 60x60 com quatro meias-cruzes. A escala vem de mask-size. */
const PLUS_TILE =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60' viewBox='0 0 60 60'%3E%3Cpath fill='%23000' d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/svg%3E\")"

export interface PlusBackgroundProps
  extends React.HTMLAttributes<HTMLDivElement> {
  /** Aresta do ladrilho, em px. */
  plusSize?: number
  /** Opacidade no anel mais denso do fade. */
  intensity?: number
}

export function PlusBackground({
  plusSize = 60,
  intensity = 0.4,
  className,
  style,
  ...props
}: PlusBackgroundProps) {
  const ladrilho = `${plusSize}px`

  return (
    <div
      aria-hidden
      // fixed e nao absolute: com absolute o elemento cobre o DOCUMENTO, e
      // numa pagina de duas dobras o fade centraliza no meio do documento —
      // o padrao sumiria no topo e no rodape. fixed prende na viewport.
      className={cn("pointer-events-none fixed inset-0 -z-10", className)}
      style={{
        // O alivio no centro nao e estetico: e o que mantem o texto do heroi
        // acima de 4.5:1 sobre o traco da cruz. O anel cheio (intensity) fica
        // a 32% do raio, onde o heroi nao tem texto.
        backgroundImage: [
          "radial-gradient(circle,",
          `hsl(var(--primary) / ${intensity * 0.3}) 0%,`,
          `hsl(var(--primary) / ${intensity}) 32%,`,
          // hsl(... / 0) e nao `transparent`: transparent e rgba(0,0,0,0), e
          // soletrar a cor da marca com alfa zero elimina qualquer duvida
          // sobre franja cinza na interpolacao
          "hsl(var(--primary) / 0) 85%)",
        ].join(" "),
        maskImage: PLUS_TILE,
        WebkitMaskImage: PLUS_TILE,
        maskRepeat: "repeat",
        WebkitMaskRepeat: "repeat",
        maskSize: ladrilho,
        WebkitMaskSize: ladrilho,
        // center porque o fade radial tambem e centrado: sem isto o centro do
        // fade cai num ponto arbitrario dentro de um ladrilho
        maskPosition: "center",
        WebkitMaskPosition: "center",
        ...style,
      }}
      {...props}
    />
  )
}
