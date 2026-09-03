import { motion, useReducedMotion } from "framer-motion"

import { Button } from "@/components/ui/button"

export interface HeroProps {
  title?: string
  subtitle?: string
  ctaLabel?: string
  /** id da seção para onde o CTA rola. */
  ctaTargetId?: string
}

export function Hero({
  title = "PulseStream",
  subtitle = "O pulso da opinião pública, em tempo real.",
  ctaLabel = "Ver análises",
  ctaTargetId = "visao-geral",
}: HeroProps) {
  const semMovimento = useReducedMotion()
  const words = title.split(" ")

  return (
    // min-h-dvh, não min-h-screen: 100vh no mobile é a altura COM a barra de
    // URL recolhida, então o herói fica alto demais e o CTA nasce fora da tela.
    // Sem bg-*: o padrão de cruzes precisa aparecer atrás daqui.
    // ATENCAO Tailwind v3: em valor arbitrario o parser converte _ em espaco,
    // e calc() EXIGE espaco em volta do sinal. Escrito sem os underscores,
    // calc(100dvh-var(--x)) e CSS invalido: nao ha erro e nao ha altura.
    <section className="flex min-h-[calc(100dvh_-_var(--altura-cabecalho))] w-full items-center justify-center px-4 py-16">
      <div className="mx-auto max-w-4xl text-center">
        <h1 className="mb-6 font-display text-6xl font-bold uppercase tracking-tight sm:text-8xl md:text-9xl">
          {words.map((word, wordIndex) => (
            <span key={wordIndex} className="mr-4 inline-block last:mr-0">
              {word.split("").map((letter, letterIndex) => (
                <motion.span
                  key={`${wordIndex}-${letterIndex}`}
                  // Roda UMA vez e para: é entrada, não loop. Isto nunca foi o
                  // que travava a página — aquilo eram as 72 paths animando
                  // pathLength/pathOffset em repeat infinito.
                  initial={semMovimento ? false : { y: 100, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={
                    semMovimento
                      ? { duration: 0 }
                      : {
                          delay: wordIndex * 0.1 + letterIndex * 0.03,
                          type: "spring",
                          stiffness: 150,
                          damping: 25,
                        }
                  }
                  className="inline-block bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent"
                >
                  {letter}
                </motion.span>
              ))}
            </span>
          ))}
        </h1>

        {/* foreground/70 e não muted-foreground: este texto fica DIRETO sobre o
            padrão, e muted-foreground sobre o traço da cruz cai para 3.6:1. */}
        <p className="mb-8 text-lg text-foreground/70">{subtitle}</p>

        <div className="group relative inline-block overflow-hidden rounded-2xl bg-gradient-to-b from-primary/20 to-primary/5 p-px shadow-lg transition-shadow duration-300 hover:shadow-xl">
          <Button
            asChild
            variant="ghost"
            className="h-auto rounded-[1.15rem] border border-border bg-card/95 px-8 py-6 text-lg font-semibold text-card-foreground transition-all duration-300 hover:bg-card group-hover:-translate-y-0.5"
          >
            {/* <a href="#..."> e não <Link>: é navegação de fragmento no mesmo
                documento. O React Router não intercepta, o browser rola, e vêm
                de graça teclado, foco-segue-fragmento (que scrollIntoView NÃO
                faz), clique do meio e "copiar link". */}
            <a href={`#${ctaTargetId}`}>
              <span className="opacity-90 transition-opacity group-hover:opacity-100">
                {ctaLabel}
              </span>
              <span
                aria-hidden
                className="ml-3 opacity-70 transition-all duration-300 group-hover:translate-x-1.5 group-hover:opacity-100"
              >
                →
              </span>
            </a>
          </Button>
        </div>
      </div>
    </section>
  )
}
