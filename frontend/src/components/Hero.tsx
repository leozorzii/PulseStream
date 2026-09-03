import { motion, useReducedMotion, type Variants } from "framer-motion"
import { ArrowRight } from "lucide-react"

import { Button } from "@/components/ui/button"

export interface HeroProps {
  title?: string
  subtitle?: string
  ctaLabel?: string
  /** id da seção para onde o CTA rola. */
  ctaTargetId?: string
  /**
   * Selo de status do pipeline, acima do título. Omitido, não renderiza.
   *
   * São DUAS strings e não uma já concatenada porque o "·" entre elas é
   * decoração: junto numa string só ele entra no nome acessível do link e o
   * leitor de tela anuncia "ponto do meio" (ou engole, dependendo do leitor).
   * Separado, leva aria-hidden.
   *
   * As strings vêm prontas de quem chama: é a regra do components/README —
   * página deriva o dado, componente recebe por prop.
   */
  selo?: {
    /** Ex.: "4 fontes ativas" */
    primario: string
    /** Ex.: "última coleta há 20 h" */
    secundario?: string
    /** Padrão: a mesma seção do CTA. */
    href?: string
  }
}

/* Entrada escalonada, à mão.
 *
 * Não existe AnimatedGroup neste repo e não vale importar um: o que ele faz
 * aqui são três elementos com atraso crescente.
 *
 * `custom` É O ATRASO EM SEGUNDOS, direto. A alternativa idiomática seria um
 * container com staggerChildren, mas as letras do <h1> definem initial/animate
 * próprios, o que INTERROMPE a propagação de variants — funcionaria, e
 * funcionaria por um detalhe de propagação que ninguém lembra ao editar.
 * Atraso explícito é auditável.
 *
 * SEM filter: blur() na entrada, apesar de a referência usar. O framer deixa
 * `filter: blur(0px)` cravado no nó depois de terminar, e filter != none cria
 * contexto de empilhamento permanente, vira bloco contentor de descendente
 * fixed e segura uma camada de composição viva. Efeito estrutural permanente
 * por 300ms de visual.
 */
/* `satisfies Variants` e não uma anotação de tipo: sem isso o TypeScript
 * alarga `type: "spring"` para `string`, e o framer só aceita o literal.
 * Com `satisfies` a inferência do literal é preservada E o formato é checado. */
const ENTRADA = {
  oculto: { opacity: 0, y: 14 },
  visivel: (atraso: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: atraso, type: "spring" as const, stiffness: 160, damping: 24 },
  }),
} satisfies Variants

export function Hero({
  title = "PulseStream",
  subtitle = "O pulso da opinião pública, em tempo real.",
  ctaLabel = "Ver análises",
  ctaTargetId = "visao-geral",
  selo,
}: HeroProps) {
  const semMovimento = useReducedMotion()
  const words = title.split(" ")

  /* Quando a última letra do título termina de entrar. Derivado do título e
     não cravado: mudar o texto não pode deixar o subtítulo nascendo em cima
     das letras ainda voando. Espelha os mesmos 0.1/0.03 do <h1> abaixo. */
  const atrasoFimTitulo =
    (words.length - 1) * 0.1 + (words[words.length - 1].length - 1) * 0.03

  return (
    /* min-h-dvh e NÃO min-h-[calc(100dvh - var(--altura-cabecalho))]: o
       cabeçalho virou `fixed` e não ocupa mais fluxo, então subtrair a altura
       dele deixa uma faixa de 64px sobrando embaixo da primeira dobra.
       dvh e não vh: 100vh no mobile é a altura COM a barra de URL recolhida.
       O pt de (cabeçalho + 4rem) contra pb-16 é o que centra opticamente:
       box-sizing é border-box, então min-h-dvh conta o padding, o box de
       conteúdo fica com 100dvh - 192px e o meio dele cai em dvh/2 + 32 —
       exatamente o centro da área visível abaixo da barra de 64px.
       pb-16 + pt-[...] em vez de py-16 + pt-[...]: com py-16 o pt sai duas
       vezes e só o twMerge decide qual vence. Funciona, mas lê como acidente.
       ATENÇÃO Tailwind v3: em valor arbitrário o parser troca _ por espaço, e
       calc() EXIGE espaço em volta do sinal. Sem os underscores é CSS
       inválido — sem erro e sem altura.
       Sem bg-*: os feixes precisam aparecer atrás daqui. */
    <section className="flex min-h-dvh w-full items-center justify-center px-4 pb-16 pt-[calc(var(--altura-cabecalho)_+_4rem)]">
      <div className="mx-auto max-w-4xl text-center">
        {selo && (
          <motion.div
            variants={ENTRADA}
            initial={semMovimento ? false : "oculto"}
            animate="visivel"
            custom={semMovimento ? 0 : 0}
            className="mb-8 flex justify-center"
          >
            {/* <a> de fragmento e não <Link>: é navegação no mesmo documento.
                O router não intercepta, o navegador rola, e vêm de graça
                teclado, foco-segue-fragmento, clique do meio e "copiar link". */}
            <a
              href={`#${selo.href ?? ctaTargetId}`}
              className="group flex w-fit items-center gap-3 rounded-full border bg-card/60 py-1 pl-4 pr-1 text-sm shadow-lg shadow-background/70 backdrop-blur-md transition-colors hover:bg-card"
            >
              <span className="text-foreground/80">{selo.primario}</span>

              {selo.secundario && (
                <>
                  {/* Separador visual, fora do nome acessível. */}
                  <span aria-hidden className="h-4 w-px bg-border" />
                  <span className="text-muted-foreground">{selo.secundario}</span>
                </>
              )}

              {/* TRUQUE DA SETA DUPLA (da referência).
                  Janela redonda de 24px com uma fileira de 48px dentro e DUAS
                  setas iguais. Em repouso a fileira está em -translate-x-1/2,
                  então a janela mostra o trecho 24→48 dela: a SEGUNDA seta. No
                  hover vai para translate-x-0 e a janela passa a mostrar 0→24:
                  a PRIMEIRA. Lê como "a seta saiu pela direita e outra entrou
                  pela esquerda", com dois nós e nenhum JS.

                  ARMADILHA: o snippet original traz só `duration-500`.
                  duration-* define transition-duration; sem uma utilidade
                  transition-*, transition-property continua `none` e o
                  transform simplesmente pula. Lá funciona porque algo acima já
                  setou a propriedade. Aqui precisa do transition-transform
                  explícito — é o detalhe que vai ser copiado errado e depurado
                  como "o framer não está funcionando".

                  motion-reduce: a seta é transição CSS pura, então o
                  useReducedMotion do framer não a alcança. A variante do
                  Tailwind alcança. Sob movimento reduzido ela troca sem
                  animar, que é o comportamento correto — não some. */}
              <span
                aria-hidden
                className="block size-6 overflow-hidden rounded-full bg-secondary transition-colors duration-500 group-hover:bg-primary/20"
              >
                <span className="flex w-12 -translate-x-1/2 transition-transform duration-500 ease-in-out group-hover:translate-x-0 motion-reduce:transition-none">
                  <span className="flex size-6">
                    <ArrowRight className="m-auto size-3 text-primary" />
                  </span>
                  <span className="flex size-6">
                    <ArrowRight className="m-auto size-3 text-primary" />
                  </span>
                </span>
              </span>
            </a>
          </motion.div>
        )}

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

        {/* text-muted-foreground de volta. Era foreground/70 porque o texto
            ficava DIRETO sobre o traço da cruz, onde muted media 3.62:1. As
            cruzes foram embora: sobre --background muted mede 6.79:1, e sobre
            o ponto mais claro dos feixes 5.76:1. */}
        <motion.p
          variants={ENTRADA}
          initial={semMovimento ? false : "oculto"}
          animate="visivel"
          custom={semMovimento ? 0 : atrasoFimTitulo + 0.12}
          className="mb-8 text-lg text-muted-foreground"
        >
          {subtitle}
        </motion.p>

        <motion.div
          variants={ENTRADA}
          initial={semMovimento ? false : "oculto"}
          animate="visivel"
          custom={semMovimento ? 0 : atrasoFimTitulo + 0.22}
          className="group relative inline-block overflow-hidden rounded-2xl bg-gradient-to-b from-primary/20 to-primary/5 p-px shadow-lg transition-shadow duration-300 hover:shadow-xl"
        >
          <Button
            asChild
            variant="ghost"
            className="h-auto rounded-[1.15rem] border bg-card/95 px-8 py-6 text-lg font-semibold text-card-foreground transition-all duration-300 hover:bg-card group-hover:-translate-y-0.5"
          >
            {/* <a href="#..."> e não <Link>: mesma razão do selo acima. */}
            <a href={`#${ctaTargetId}`}>
              <span className="opacity-90 transition-opacity group-hover:opacity-100">
                {ctaLabel}
              </span>
              {/* A seta simples fica: a dupla é o gesto do SELO, e repetir o
                  mesmo truque a 40px de distância anula os dois. */}
              <span
                aria-hidden
                className="ml-3 opacity-70 transition-all duration-300 group-hover:translate-x-1.5 group-hover:opacity-100"
              >
                →
              </span>
            </a>
          </Button>
        </motion.div>
      </div>
    </section>
  )
}
