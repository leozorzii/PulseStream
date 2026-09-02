import { Link, NavLink, Outlet } from "react-router-dom"

import { cn } from "@/lib/utils"

const rotas = [
  { to: "/dashboard", label: "Dashboard" },
]

/** Casca das telas de dados: navegação fixa + <Outlet/>. A landing fica
 *  FORA deste layout, porque o hero é full-bleed e não quer barra em cima. */
export default function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <nav className="container mx-auto flex items-center gap-6 px-4 py-4">
          <Link to="/" className="text-lg font-semibold tracking-tight">
            Pulse<span className="text-primary">Stream</span>
          </Link>

          <div className="flex items-center gap-4 text-sm">
            {rotas.map((rota) => (
              <NavLink
                key={rota.to}
                to={rota.to}
                className={({ isActive }) =>
                  cn(
                    "transition-colors hover:text-foreground",
                    isActive ? "text-foreground" : "text-muted-foreground"
                  )
                }
              >
                {rota.label}
              </NavLink>
            ))}
          </div>
        </nav>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
