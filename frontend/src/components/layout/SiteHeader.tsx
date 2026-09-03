import { motion, useReducedMotion } from "framer-motion"
import { Link } from "react-router-dom"

import { MobileNav } from "@/components/layout/MobileNav"
import { NavMenu } from "@/components/layout/NavMenu"
import { PeriodoFiltro } from "@/components/PeriodoFiltro"
import { StatusPill, type EstadoColeta } from "@/components/StatusPill"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { Periodo } from "@/lib/periodo"
import type { Fonte } from "@/lib/mock"

/*
 * CABEÇALHO FLUTUANTE, 100% TRANSPARENTE
 * --------------------------------------
 * A BARRA não tem fundo, borda nem backdrop-blur, em nenhuma posição de
 * rolagem. Quem flutua são as ILHAS de controle.
 *
 * POR QUE AS ILHAS TÊM SUPERFÍCIE E A BARRA NÃO
 * O problema de uma barra transparente NÃO é contraste. Medido sobre
 * --background: link de nav em text-foreground/60 dá 6.26:1, a marca em
 * foreground cheia dá 16.09:1, text-primary dá 5.72:1; sobre o ponto mais
 * claro dos feixes caem só para 5.31 / ~14 / ~5.2. Nada reprova.
 * O problema é OCLUSÃO. Com bg-card/80 + blur, o que rolava por baixo era
 * achatado num substrato previsível. Sem superfície nenhuma, o texto do
 * cabeçalho passa por cima de conteúdo arbitrário: painéis bg-card, as áreas
 * empilhadas coloridas do SentimentTrendChart, numerais de KPI quase brancos.
 * text-foreground/60 sobre um rótulo de gráfico não é "razão baixa", são dois
 * textos um em cima do outro. Cor mais forte não resolve; superfície resolve.
 * Daí a receita ILHA abaixo: é EXATAMENTE o bg-card/80 + backdrop-blur-md que
 * o header tinha, recortado em pedaços. Não foi enfraquecido, foi fatiado.
 *
 * pointer-events-none NA BARRA, auto NAS ILHAS
 * Uma faixa fixed, largura total, 64px, totalmente invisível engole TODO
 * clique e TODA seleção de texto nos primeiros 64px de qualquer página, sem
 * nenhuma pista visual de que está ali. Esta é a regressão nº 1 do desenho.
 *
 * z-40 CONTINUA BASTANDO
 * O comentário antigo creditava ao backdrop-blur a criação do contexto de
 * empilhamento que escopa o z-50 do dropdown. Era verdade e era redundante:
 * elemento POSICIONADO com z-index != auto já cria contexto sozinho. Tirar o
 * blur não muda nada aqui.
 *
 * NADA DE transform/filter/contain NO <header>
 * Qualquer um dos três transforma o header em bloco contentor de descendente
 * `position: fixed` — e o painel do MobileNav agora é fixed. Por isso a
 * animação de entrada vai nas ILHAS, nunca na barra. Se um dia alguém quiser
 * "fazer o header aparecer com fade", é aqui que quebra.
 *
 * ALTURA VEM DO CSS, não do JS
 * Antes eram duas fontes do mesmo número: style={{height: ALTURA_CABECALHO}}
 * daqui e --altura-cabecalho no index.css. Agora h-[--altura-cabecalho] lê a
 * var direto; ALTURA_CABECALHO fica só como fallback do useScrollSpy, que é o
 * papel que ele já exercia de fato.
 *
 * top-0 E BANDA DE 64px, e não uma barra recuada com top-3: com recuo a banda
 * que oclui vira 12px + altura da pílula (~52px) enquanto --altura-cabecalho
 * continua dizendo 64, e aí scroll-padding-top, centragem do herói e o padding
 * de cada rota passam a descrever uma faixa que não existe. Visualmente dá no
 * mesmo — as pílulas de ~40px ficam centradas na banda.
 */

/** Superfície das ilhas. Mesmo material dos cards do app (border + bg-card),
 *  só que redondo — para as ilhas lerem como a mesma matéria, não como um
 *  elemento novo. */
const ILHA = "rounded-full border bg-card/80 shadow-lg shadow-background/70 backdrop-blur-md"

export function SiteHeader({
  secaoAtiva,
  fontes,
  periodo,
  onPeriodo,
  estadoColeta,
  detalheColeta,
  onColetarTudo,
}: {
  secaoAtiva: string | null
  fontes: Fonte[]
  periodo: Periodo
  onPeriodo: (p: Periodo) => void
  estadoColeta: EstadoColeta
  detalheColeta?: string
  onColetarTudo?: () => void
}) {
  const semMovimento = useReducedMotion()

  return (
    <header className="pointer-events-none fixed inset-x-0 top-0 z-40 h-[--altura-cabecalho]">
      <div className="relative mx-auto flex h-full max-w-[1400px] items-center gap-3 px-4">
        {/* Ilha da esquerda: marca + navegação de seção. */}
        <motion.div
          className={cn("pointer-events-auto flex items-center gap-1 pl-4 pr-2", ILHA)}
          initial={semMovimento ? false : { opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={
            semMovimento ? { duration: 0 } : { duration: 0.35, ease: "easeOut" }
          }
        >
          <Link
            to="/"
            className="shrink-0 py-2 font-display text-lg font-semibold uppercase tracking-wide"
          >
            Pulse<span className="text-primary">Stream</span>
          </Link>

          {/* A navegação entra NA MESMA ilha da marca, e não numa própria: são
              dois grupos de ~250px e ~300px que ficariam com um vão de 12px
              entre si — leitura de "duas coisas quebradas", não de "duas
              coisas". */}
          <div className="ml-2 hidden md:block">
            <NavMenu secaoAtiva={secaoAtiva} fontes={fontes} />
          </div>
        </motion.div>

        <motion.div
          className="pointer-events-auto ml-auto flex items-center gap-3"
          initial={semMovimento ? false : { opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={
            semMovimento
              ? { duration: 0 }
              : { duration: 0.35, delay: 0.06, ease: "easeOut" }
          }
        >
          {/* Cada controle da direita é uma ilha própria: eles têm larguras
              muito diferentes e agrupá-los devolveria uma barra — que é
              exatamente o que a decisão do desenho removeu. */}
          <PeriodoFiltro
            valor={periodo}
            onChange={onPeriodo}
            className={cn("hidden p-1 sm:flex", ILHA)}
          />

          <StatusPill
            estado={estadoColeta}
            detalhe={detalheColeta}
            className={cn("hidden lg:inline-flex", ILHA)}
          />

          {/* Já é opaco (bg-primary, 5.72:1 sobre o fundo) — não precisa da
              ILHA, precisa só de sombra para descolar e de raio redondo para
              concordar com os vizinhos. */}
          <Button
            size="sm"
            onClick={onColetarTudo}
            disabled={estadoColeta !== "ocioso"}
            className="hidden rounded-full shadow-lg shadow-background/70 sm:inline-flex"
          >
            Coletar tudo
          </Button>

          <MobileNav fontes={fontes} classeIlha={ILHA} />
        </motion.div>
      </div>
    </header>
  )
}
