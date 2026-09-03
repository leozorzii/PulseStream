import * as React from "react"

import { cn } from "@/lib/utils"
import { SENTIMENT, SENTIMENT_ORDER, type SentimentLabel } from "@/lib/sentiment"
import type { PostAnalisado } from "@/lib/mock"

/*
 * O painel de evidência.
 *
 * É o que separa um dashboard em que se acredita de um em que não: "64%
 * negativo" é uma afirmação, e ninguém age sobre uma afirmação sem poder ver
 * a frase que a gerou. Aqui o número vira texto que a pessoa lê.
 */
export function PostsFeed({ posts }: { posts: PostAnalisado[] }) {
  const [filtro, setFiltro] = React.useState<SentimentLabel | "TODOS">("TODOS")

  const visiveis = filtro === "TODOS" ? posts : posts.filter((p) => p.sentiment.label === filtro)

  return (
    <div className="rounded-xl border bg-card">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <h3 className="font-display text-lg font-semibold uppercase tracking-wide">
          Posts recentes
        </h3>

        {/* Filtros numa linha só, acima do conteúdo — é onde as diretrizes de
            visualização pedem que controle de recorte fique. */}
        <div className="flex flex-wrap items-center gap-1">
          <BotaoFiltro ativo={filtro === "TODOS"} onClick={() => setFiltro("TODOS")}>
            Todos
          </BotaoFiltro>
          {SENTIMENT_ORDER.map((tone) => {
            const { label, icon: Icone, textClass } = SENTIMENT[tone]
            return (
              <BotaoFiltro key={tone} ativo={filtro === tone} onClick={() => setFiltro(tone)}>
                <Icone className={cn("h-3.5 w-3.5", textClass)} aria-hidden />
                {label}
              </BotaoFiltro>
            )
          })}
        </div>
      </div>

      {visiveis.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-muted-foreground">
          Nenhum post com esse sentimento no período.
        </p>
      ) : (
        <ul className="divide-y divide-border">
          {visiveis.map((post) => (
            <ItemPost key={post.id} post={post} />
          ))}
        </ul>
      )}
    </div>
  )
}

function ItemPost({ post }: { post: PostAnalisado }) {
  const { label, textClass, icon: Icone } = SENTIMENT[post.sentiment.label]

  return (
    <li className="px-5 py-4">
      <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
        {/* ícone + rótulo junto da cor: a codificação secundária que torna a
            paleta legível para quem não distingue verde de vermelho */}
        <span className={cn("flex items-center gap-1.5 font-medium", textClass)}>
          <Icone className="h-3.5 w-3.5" aria-hidden />
          {label}
        </span>
        <span className="tabular-nums text-muted-foreground">
          {post.sentiment.polarity_score > 0 ? "+" : ""}
          {post.sentiment.polarity_score.toFixed(2)}
        </span>
        <span className="text-muted-foreground">·</span>
        <span className="text-muted-foreground">{post.source.name}</span>
        <span className="text-muted-foreground">·</span>
        <time className="text-muted-foreground" dateTime={post.published_at}>
          {new Date(post.published_at).toLocaleString("pt-BR", {
            day: "2-digit",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </time>
      </div>

      <p className="text-sm leading-relaxed">{post.text_content}</p>

      {post.sentiment.extracted_keywords.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {post.sentiment.extracted_keywords.map((termo) => (
            <li
              key={termo}
              className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
            >
              {termo}
            </li>
          ))}
        </ul>
      )}
    </li>
  )
}

function BotaoFiltro({
  ativo,
  onClick,
  children,
}: {
  ativo: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={ativo}
      className={cn(
        "flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs transition-colors",
        ativo
          ? "bg-secondary text-secondary-foreground"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      {children}
    </button>
  )
}
