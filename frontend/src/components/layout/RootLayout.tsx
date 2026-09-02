import { Outlet } from "react-router-dom"

import { PlusBackground } from "@/components/PlusBackground"

/** Casca única do app. Sem barra de navegação: o app é uma página só, e o
 *  herói é full-bleed — uma nav de um link só em cima dele seria ruído.
 *
 *  Existe para montar o fundo UMA vez, fora do ciclo de vida das rotas. Se o
 *  PlusBackground vivesse dentro de cada página, remontaria a cada navegação
 *  e a camada mascarada seria rasterizada de novo à toa.
 *
 *  Sem bg-background aqui, de propósito. O <body> já pinta o fundo e essa cor
 *  propaga para o canvas, que fica ATRÁS do -z-10 do padrão. Um bg-background
 *  nesta div, que é conteúdo em fluxo, ficaria NA FRENTE e apagaria o padrão
 *  inteiro — sem erro nenhum, só uma página lisa. */
export default function RootLayout() {
  return (
    <div className="min-h-dvh">
      <PlusBackground />
      <Outlet />
    </div>
  )
}
