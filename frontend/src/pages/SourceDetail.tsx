import { Link, useParams } from "react-router-dom"

/** Placeholder. A tela real entra quando os hooks de fetch existirem.
 *  O container/padding mora aqui agora: antes vinha do AppLayout, que virou
 *  uma casca sem cromo — sem isto a página encostaria na borda da viewport. */
export default function SourceDetail() {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="container mx-auto px-4 py-16">
      <Link to="/" className="text-sm text-primary hover:underline">
        ← Voltar
      </Link>

      <h1 className="mt-4 font-display text-3xl font-semibold uppercase tracking-wide">Fonte {id}</h1>
      <p className="mt-1 text-sm text-foreground/70">
        Detalhe da fonte — ainda não implementado.
      </p>
    </div>
  )
}
