import {
  AtSign,
  Camera,
  MessageSquare,
  Newspaper,
  Video,
  type LucideIcon,
} from "lucide-react"

import type { Plataforma } from "@/lib/mock"

/* O lucide removeu os ícones de marca (Instagram, Twitter, YouTube) por
 * questão de marca registrada, então usamos genéricos que descrevem o MEIO
 * em vez da empresa — o que envelhece melhor de qualquer forma.
 *
 * Este mapa era privado do SourcesTable; saiu para cá quando o dropdown da
 * navbar passou a precisar dos mesmos ícones. Duas cópias divergiriam. */
export const PLATAFORMA: Record<Plataforma, { rotulo: string; icone: LucideIcon }> = {
  NEWS: { rotulo: "Portal de Notícias", icone: Newspaper },
  YOUTUBE: { rotulo: "YouTube", icone: Video },
  TWITTER: { rotulo: "Twitter / X", icone: AtSign },
  INSTAGRAM: { rotulo: "Instagram", icone: Camera },
  REDDIT: { rotulo: "Reddit", icone: MessageSquare },
}
