import { Route, Routes } from "react-router-dom"

import AppLayout from "@/components/layout/AppLayout"
import Dashboard from "@/pages/Dashboard"
import Landing from "@/pages/Landing"
import NotFound from "@/pages/NotFound"
import SourceDetail from "@/pages/SourceDetail"

export default function App() {
  return (
    <Routes>
      {/* A landing fica fora do AppLayout: o hero é full-bleed e não quer
          barra de navegação em cima. */}
      <Route path="/" element={<Landing />} />

      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/sources/:id" element={<SourceDetail />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
