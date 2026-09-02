import { useParams } from "react-router-dom"

/** Placeholder. A tela real entra quando os hooks de fetch existirem. */
export default function SourceDetail() {
  const { id } = useParams<{ id: string }>()

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Fonte {id}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Detalhe da fonte — ainda não implementado.
      </p>
    </div>
  )
}
