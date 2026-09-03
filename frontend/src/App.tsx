import { Route, Routes } from "react-router-dom"

import RootLayout from "@/components/layout/RootLayout"
import Home from "@/pages/Home"
import NotFound from "@/pages/NotFound"
import SourceDetail from "@/pages/SourceDetail"

export default function App() {
  return (
    <Routes>
      {/* Uma casca só, que não desenha cromo nenhum — existe para montar o
          fundo uma vez. O app é página única, mas o router fica: /sources/:id
          precisa ser link compartilhável, e o catch-all precisa existir. */}
      <Route element={<RootLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/sources/:id" element={<SourceDetail />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
