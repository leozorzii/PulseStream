import { motion, useReducedMotion } from "framer-motion"
import { Link } from "react-router-dom"

import { Button } from "@/components/ui/button"

function FloatingPaths({ position }: { position: number }) {
  const semMovimento = useReducedMotion()

  const paths = Array.from({ length: 36 }, (_, i) => ({
    id: i,
    d: `M-${380 - i * 5 * position} -${189 + i * 6}C-${
      380 - i * 5 * position
    } -${189 + i * 6} -${312 - i * 5 * position} ${216 - i * 6} ${
      152 - i * 5 * position
    } ${343 - i * 6}C${616 - i * 5 * position} ${470 - i * 6} ${
      684 - i * 5 * position
    } ${875 - i * 6} ${684 - i * 5 * position} ${875 - i * 6}`,
    width: 0.5 + i * 0.03,
    // duracao derivada do indice, nao de Math.random(): aleatorio no render
    // faz cada re-render sortear um valor novo e a animacao reiniciar sozinha.
    // O modulo espalha as duracoes entre 20s e 30s do mesmo jeito, mas estavel.
    duration: 20 + ((i * 7) % 11),
  }))

  return (
    <div className="pointer-events-none absolute inset-0">
      {/* as paths pintam com currentColor: a cor vem daqui, do teal da marca */}
      <svg
        className="h-full w-full text-primary/40"
        viewBox="0 0 696 316"
        fill="none"
      >
        <title>Background Paths</title>
        {paths.map((path) => (
          <motion.path
            key={path.id}
            d={path.d}
            stroke="currentColor"
            strokeWidth={path.width}
            strokeOpacity={0.1 + path.id * 0.03}
            initial={{ pathLength: 0.3, opacity: 0.6 }}
            // animação em loop infinito é exatamente o caso que
            // prefers-reduced-motion existe para cobrir
            animate={
              semMovimento
                ? { pathLength: 1, opacity: 0.5 }
                : { pathLength: 1, opacity: [0.3, 0.6, 0.3], pathOffset: [0, 1, 0] }
            }
            transition={
              semMovimento
                ? { duration: 0 }
                : {
                    duration: path.duration,
                    repeat: Number.POSITIVE_INFINITY,
                    ease: "linear",
                  }
            }
          />
        ))}
      </svg>
    </div>
  )
}

export function BackgroundPaths({
  title = "PulseStream",
  subtitle = "O pulso da opinião pública, em tempo real.",
  ctaLabel = "Abrir dashboard",
  ctaTo = "/dashboard",
}: {
  title?: string
  subtitle?: string
  ctaLabel?: string
  ctaTo?: string
}) {
  const words = title.split(" ")

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-background">
      <div className="absolute inset-0">
        <FloatingPaths position={1} />
        <FloatingPaths position={-1} />
      </div>

      <div className="container relative z-10 mx-auto px-4 text-center md:px-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2 }}
          className="mx-auto max-w-4xl"
        >
          <h1 className="mb-6 text-5xl font-bold tracking-tighter sm:text-7xl md:text-8xl">
            {words.map((word, wordIndex) => (
              <span key={wordIndex} className="mr-4 inline-block last:mr-0">
                {word.split("").map((letter, letterIndex) => (
                  <motion.span
                    key={`${wordIndex}-${letterIndex}`}
                    initial={{ y: 100, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{
                      delay: wordIndex * 0.1 + letterIndex * 0.03,
                      type: "spring",
                      stiffness: 150,
                      damping: 25,
                    }}
                    className="inline-block bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent"
                  >
                    {letter}
                  </motion.span>
                ))}
              </span>
            ))}
          </h1>

          <p className="mb-8 text-lg text-muted-foreground">{subtitle}</p>

          <div className="group relative inline-block overflow-hidden rounded-2xl bg-gradient-to-b from-primary/20 to-primary/5 p-px shadow-lg backdrop-blur-lg transition-shadow duration-300 hover:shadow-xl">
            <Button
              asChild
              variant="ghost"
              className="h-auto rounded-[1.15rem] border border-border bg-card/95 px-8 py-6 text-lg font-semibold text-card-foreground transition-all duration-300 hover:bg-card group-hover:-translate-y-0.5"
            >
              <Link to={ctaTo}>
                <span className="opacity-90 transition-opacity group-hover:opacity-100">
                  {ctaLabel}
                </span>
                <span className="ml-3 opacity-70 transition-all duration-300 group-hover:translate-x-1.5 group-hover:opacity-100">
                  →
                </span>
              </Link>
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
