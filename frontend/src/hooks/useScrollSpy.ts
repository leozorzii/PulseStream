import * as React from "react"

/**
 * Qual das seções está sendo lida agora.
 *
 * A seção ativa é a ÚLTIMA cujo topo já passou pela linha de âncora — a mesma
 * linha que o scroll-padding-top usa. Essa é a semântica que corresponde ao
 * que a pessoa está de fato lendo.
 *
 * DUAS TENTATIVAS ANTERIORES, E POR QUE FALHARAM
 *
 * 1. "a primeira seção visível em ordem de documento" ficava atrasada em uma:
 *    com a faixa de observação começando logo abaixo do cabeçalho, a CAUDA da
 *    seção anterior ainda ocupava a faixa e vencia o desempate.
 *
 * 2. IntersectionObserver sozinho perdia atualizações. O observer só dispara
 *    em CRUZAMENTO de limiar, e uma rolagem suave que termina sem cruzar nada
 *    — clicar numa âncora e parar — deixava o indicador no valor anterior.
 *
 * Por isso: listener de scroll, mas estrangulado por requestAnimationFrame.
 * O medo legítimo com listener de scroll é rodar trabalho pesado a cada pixel;
 * com rAF ele roda no máximo uma vez por frame, e o trabalho são quatro
 * getBoundingClientRect. Isso é barato — o que derrubou a landing deste
 * projeto foi animar 72 paths SVG em loop, não ler quatro retângulos.
 */
export function useScrollSpy(ids: string[], deslocamentoTopo = 0): string | null {
  const [ativo, setAtivo] = React.useState<string | null>(ids[0] ?? null)

  // Serializa para a dependência não mudar por identidade de array a cada
  // render — quem chama costuma passar literal.
  const chave = ids.join("|")

  React.useEffect(() => {
    const lista = chave.split("|").filter(Boolean)
    let frame = 0

    const recalcular = () => {
      frame = 0

      const elementos = lista
        .map((id) => document.getElementById(id))
        .filter((el): el is HTMLElement => el !== null)

      if (elementos.length === 0) return

      /* O limite tem que ser o MESMO valor do scroll-padding-top do html, não
       * a altura do cabeçalho: scrollIntoView respeita o scroll-padding, então
       * o topo da seção para em 80px (64 do header + 1rem). Comparar contra 64
       * fazia a seção anterior continuar vencendo. Lendo do CSS, os dois não
       * podem divergir quando um deles mudar. */
      const padding = parseFloat(
        getComputedStyle(document.documentElement).scrollPaddingTop
      )
      const limite = (Number.isNaN(padding) ? deslocamentoTopo : padding) + 2

      let atual = elementos[0].id
      for (const el of elementos) {
        if (el.getBoundingClientRect().top <= limite) atual = el.id
        else break
      }

      // A última seção pode ser curta demais para o topo dela cruzar o limite,
      // e ficaria eternamente sem marcar. Chegando ao fim, é ela que está
      // sendo lida. O `scrollY > 0` importa: na primeira execução o layout
      // ainda não assentou e a página no topo se consideraria no fim.
      const fim =
        window.scrollY > 0 &&
        window.scrollY + window.innerHeight >=
          document.documentElement.scrollHeight - 2
      if (fim) atual = elementos[elementos.length - 1].id

      setAtivo(atual)
    }

    const agendar = () => {
      if (frame) return
      frame = requestAnimationFrame(recalcular)
    }

    // passive: avisa ao navegador que não haverá preventDefault, então ele não
    // precisa esperar o handler para começar a rolar
    window.addEventListener("scroll", agendar, { passive: true })
    window.addEventListener("resize", agendar)
    recalcular()

    return () => {
      window.removeEventListener("scroll", agendar)
      window.removeEventListener("resize", agendar)
      if (frame) cancelAnimationFrame(frame)
    }
  }, [chave, deslocamentoTopo])

  return ativo
}
