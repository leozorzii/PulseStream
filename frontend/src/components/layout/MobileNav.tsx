import * as React from "react"
import { Menu, X } from "lucide-react"
import { Link, useLocation } from "react-router-dom"

import { SECOES } from "@/lib/nav"
import { cn } from "@/lib/utils"
import type { Fonte } from "@/lib/mock"

/** Disclosure simples, não modal — por isso nada de Radix Dialog aqui: a
 *  armadilha de foco e o portal dele existem para diálogo, e isto é uma lista
 *  de links. Sem layoutId de propósito: o nav desktop fica `hidden`, não
 *  desmontado, e duas instâncias vivas do mesmo layoutId fariam o framer
 *  interpolar contra uma caixa de tamanho zero. */
export function MobileNav({
  fontes,
  classeIlha,
}: {
  fontes: Fonte[]
  classeIlha?: string
}) {
  const [aberto, setAberto] = React.useState(false)
  const { pathname } = useLocation()
  const naHome = pathname === "/"

  React.useEffect(() => {
    if (!aberto) return
    const aoTeclar = (e: KeyboardEvent) => e.key === "Escape" && setAberto(false)
    document.addEventListener("keydown", aoTeclar)
    return () => document.removeEventListener("keydown", aoTeclar)
  }, [aberto])

  return (
    <>
      <button
        type="button"
        onClick={() => setAberto((v) => !v)}
        aria-expanded={aberto}
        aria-label={aberto ? "Fechar menu" : "Abrir menu"}
        className={cn(
          "p-2 text-foreground/70 transition-colors hover:text-foreground md:hidden",
          classeIlha
        )}
      >
        {aberto ? <X className="h-5 w-5" aria-hidden /> : <Menu className="h-5 w-5" aria-hidden />}
      </button>

      {aberto && (
        /* fixed, não absolute: antes o painel colava na borda de baixo do
           container interno do header — com a barra flutuante isso é "colado
           numa barra que não é desenhada", e o border-b prometia um encaixe
           que sumiu. É legal aninhar fixed em fixed: position:fixed sozinho
           NÃO cria bloco contentor para descendente fixed; só transform,
           filter e contain:paint criam — por isso o SiteHeader proíbe os três.
           pointer-events-auto explícito porque o <header> é none e herda. */
        <div className="pointer-events-auto fixed inset-x-4 top-[calc(var(--altura-cabecalho)_+_0.5rem)] z-50 overflow-hidden rounded-2xl border bg-popover shadow-xl md:hidden">
          <nav aria-label="Menu">
            <ul className="py-2">
              {SECOES.map((secao) => (
                <li key={secao.id}>
                  {naHome ? (
                    <a
                      href={`#${secao.id}`}
                      onClick={() => setAberto(false)}
                      className="block px-4 py-2.5 text-sm hover:bg-muted"
                    >
                      {secao.titulo}
                    </a>
                  ) : (
                    <Link
                      to={`/#${secao.id}`}
                      onClick={() => setAberto(false)}
                      className="block px-4 py-2.5 text-sm hover:bg-muted"
                    >
                      {secao.titulo}
                    </Link>
                  )}
                </li>
              ))}

              <li className="mt-1 border-t border-border pt-1">
                <p className="px-4 py-1.5 text-xs uppercase tracking-wider text-foreground/50">
                  Fontes
                </p>
              </li>
              {fontes.map((fonte) => (
                <li key={fonte.id}>
                  <Link
                    to={`/sources/${fonte.id}`}
                    onClick={() => setAberto(false)}
                    className={cn(
                      "block px-4 py-2.5 text-sm hover:bg-muted",
                      !fonte.is_active && "text-foreground/50"
                    )}
                  >
                    {fonte.name}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      )}
    </>
  )
}
