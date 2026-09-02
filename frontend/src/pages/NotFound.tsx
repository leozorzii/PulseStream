import { Link } from "react-router-dom"

import { Button } from "@/components/ui/button"

/** Sem bg-background aqui: seria opaco em conteúdo em fluxo e apagaria o
 *  padrão de cruzes, que vive numa camada -z-10 atrás. */
export default function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-4 text-center">
      <p className="text-sm font-medium text-primary">404</p>
      <h1 className="text-3xl font-semibold tracking-tight">Página não encontrada</h1>
      <p className="text-foreground/70">
        O endereço acessado não existe neste app.
      </p>
      <Button asChild className="mt-2">
        <Link to="/">Voltar ao início</Link>
      </Button>
    </div>
  )
}
