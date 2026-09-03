import * as React from "react"
import { AnimatePresence, motion, useReducedMotion } from "framer-motion"
import { ChevronDown } from "lucide-react"
import { Link, useLocation } from "react-router-dom"

import { cn } from "@/lib/utils"
import { PLATAFORMA } from "@/lib/plataforma"
import { SECOES } from "@/lib/nav"
import type { Fonte } from "@/lib/mock"

/*
 * NAVEGAÇÃO DE SEÇÃO, COM INDICADOR DESLIZANTE
 * --------------------------------------------
 * Adaptado do componente de referência do 21st.dev. O que mudou e por quê:
 *
 * - O painel do dropdown NÃO tem layoutId. No original ele dividia o id
 *   'cursor' com o sublinhado, e o framer trata id compartilhado como o MESMO
 *   elemento lógico: ele tentava transformar um traço de 2px num painel de
 *   256px. layoutId só se paga quando duas instâncias do mesmo elemento
 *   trocam de posição; aqui o painel só entra e sai, então é AnimatePresence
 *   com opacidade e deslocamento.
 * - O sublinhado ganhou pointer-events-none. Sem isso o cursor entrando nele
 *   dispara mouseleave no link, que o desmonta, que reentra no link — um laço
 *   de oscilação de 2px.
 * - O sublinhado ganhou inset explícito. `absolute` com insets automáticos
 *   resolve para a posição estática: funcionava por acidente e quebraria no
 *   primeiro ajuste de padding.
 * - O painel ganhou z-50. Todo <li> é relative com z-index auto, logo nenhum
 *   cria contexto de empilhamento, e o painel pintava em ordem de árvore
 *   contra os <li> seguintes — o item ao lado cobria o menu.
 * - Abre por clique/teclado, não só por hover: hover puro é inacessível por
 *   teclado e morto no toque, onde o primeiro toque navega em vez de abrir.
 * - O painel usa bg-popover, não bg-background. Fundo opaco em conteúdo é a
 *   regra que este projeto proíbe — apagaria o padrão de cruzes atrás.
 * - O indicador é barrado sob prefers-reduced-motion. O framer NÃO desativa
 *   animação de layoutId sozinho, ao contrário do que se supõe.
 */

export function NavMenu({
  secaoAtiva,
  fontes,
}: {
  secaoAtiva: string | null
  fontes: Fonte[]
}) {
  const semMovimento = useReducedMotion()
  const [aberto, setAberto] = React.useState(false)
  const { pathname } = useLocation()
  const naHome = pathname === "/"

  return (
    <nav aria-label="Seções do painel">
      <ul className="flex items-center">
        {SECOES.map((secao) => {
          const ativo = secaoAtiva === secao.id
          const ehFontes = secao.id === "fontes"

          return (
            <li key={secao.id} className="relative">
              <div className="flex items-center">
                <LinkSecao id={secao.id} naHome={naHome} ativo={ativo}>
                  {secao.titulo}
                </LinkSecao>

                {ehFontes && (
                  <BotaoDropdown aberto={aberto} onToggle={() => setAberto((v) => !v)} />
                )}
              </div>

              {ativo && (
                <motion.span
                  // Só o sublinhado usa layoutId: ele de fato desliza entre
                  // irmãos, que é o único caso em que layout compartilhado
                  // se paga.
                  layoutId={semMovimento ? undefined : "indicador-nav"}
                  className="pointer-events-none absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-primary"
                  transition={{ type: "spring", stiffness: 380, damping: 32 }}
                />
              )}

              {ehFontes && (
                <DropdownFontes
                  aberto={aberto}
                  fechar={() => setAberto(false)}
                  fontes={fontes}
                  semMovimento={!!semMovimento}
                />
              )}
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

/** Em "/" é âncora de fragmento pura — o navegador rola e o foco segue o
 *  destino. Em /sources/:id vira Link, porque não há seção nenhuma para
 *  ancorar naquela rota. */
function LinkSecao({
  id,
  naHome,
  ativo,
  children,
}: {
  id: string
  naHome: boolean
  ativo: boolean
  children: React.ReactNode
}) {
  const classe = cn(
    "rounded-md px-3 py-2 text-sm transition-colors",
    ativo ? "text-foreground" : "text-foreground/60 hover:text-foreground"
  )

  if (naHome) {
    return (
      <a href={`#${id}`} className={classe} aria-current={ativo ? "true" : undefined}>
        {children}
      </a>
    )
  }

  return (
    <Link to={`/#${id}`} className={classe}>
      {children}
    </Link>
  )
}

function BotaoDropdown({ aberto, onToggle }: { aberto: boolean; onToggle: () => void }) {
  const idPainel = React.useId()

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={aberto}
      // useId do React 19 gera «r0»: id HTML válido, mas NÃO é seletor CSS
      // válido. Serve para aria-controls; nunca usar em querySelector.
      aria-controls={idPainel}
      aria-label={aberto ? "Fechar lista de fontes" : "Abrir lista de fontes"}
      className="-ml-1 rounded-md p-1 text-foreground/60 transition-colors hover:text-foreground"
    >
      <ChevronDown
        className={cn("h-4 w-4 transition-transform", aberto && "rotate-180")}
        aria-hidden
      />
    </button>
  )
}

function DropdownFontes({
  aberto,
  fechar,
  fontes,
  semMovimento,
}: {
  aberto: boolean
  fechar: () => void
  fontes: Fonte[]
  semMovimento: boolean
}) {
  const ref = React.useRef<HTMLDivElement>(null)

  // Escape fecha e clique fora fecha. Um menu que só fecha ao reclicar o
  // gatilho prende o usuário — e Escape é o que o teclado espera.
  React.useEffect(() => {
    if (!aberto) return

    const aoTeclar = (e: KeyboardEvent) => {
      if (e.key === "Escape") fechar()
    }
    const aoClicar = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) fechar()
    }

    document.addEventListener("keydown", aoTeclar)
    document.addEventListener("mousedown", aoClicar)
    return () => {
      document.removeEventListener("keydown", aoTeclar)
      document.removeEventListener("mousedown", aoClicar)
    }
  }, [aberto, fechar])

  return (
    <AnimatePresence>
      {aberto && (
        <motion.div
          ref={ref}
          // Sem layout nem layoutId: o painel não morfa em nada, só entra e
          // sai. E layout + animate={{y}} disputariam o mesmo transform.
          initial={semMovimento ? false : { opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={semMovimento ? { opacity: 0 } : { opacity: 0, y: -6 }}
          transition={{ duration: 0.16, ease: "easeOut" }}
          // z-50 porque nenhum <li> cria contexto de empilhamento: sem isto o
          // item seguinte pinta por cima do painel.
          className="absolute left-0 top-full z-50 mt-2 w-72 overflow-hidden rounded-lg border border-border bg-popover shadow-xl"
        >
          {/* Lista de links, não role="menu": menu promete navegação por setas
              com roving tabindex, semântica de aplicação — errado para links. */}
          <ul className="py-1">
            {fontes.map((fonte) => {
              const { icone: Icone, rotulo } = PLATAFORMA[fonte.plataform]
              return (
                <li key={fonte.id}>
                  <Link
                    to={`/sources/${fonte.id}`}
                    onClick={fechar}
                    className="flex items-center gap-3 px-3 py-2.5 text-sm transition-colors hover:bg-muted"
                  >
                    <Icone className="h-4 w-4 shrink-0 text-foreground/60" aria-hidden />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-popover-foreground">
                        {fonte.name}
                      </span>
                      <span className="block truncate text-xs text-foreground/60">
                        {rotulo}
                        {!fonte.is_active && " · pausada"}
                      </span>
                    </span>
                    <span className="shrink-0 tabular-nums text-xs text-foreground/60">
                      {fonte.post_count}
                    </span>
                  </Link>
                </li>
              )
            })}

            <li className="mt-1 border-t border-border pt-1">
              <a
                href="#fontes"
                onClick={fechar}
                className="block px-3 py-2.5 text-sm text-primary transition-colors hover:bg-muted"
              >
                Ver todas as fontes
              </a>
            </li>
          </ul>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
