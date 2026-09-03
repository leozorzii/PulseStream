import { cn } from "@/lib/utils"

/*
 * FEIXES DE LUZ — o fundo de todo o app.
 *
 * Substitui o PlusBackground (padrão de cruzes). Adaptado do componente de
 * referência do 21st.dev; o que mudou, e por quê:
 *
 * 1. A REFERÊNCIA HOTLINKA UM JPEG DE 3276x4095 DO cdn.21st.dev. Não usamos:
 *    é asset de terceiro, sem controle de disponibilidade, e pesa mais que
 *    todo o bundle. Sem a foto, o gradiente de fade muda de função — ver (3).
 *
 * 2. `var(--background)` CRU NÃO FUNCIONA AQUI. Nossos tokens são triplas HSL
 *    sem wrapper ("200 20% 6%"). Como parada de cor isso é inválido, o que
 *    invalida o radial-gradient() inteiro, o que faz o navegador descartar a
 *    declaração `background` toda. Sem erro, sem pintura, sem pista. Tem que
 *    ser hsl(var(--background)). E `hsl(var(--x) / 0)` em vez da palavra
 *    `transparent`, que é rgba(0,0,0,0) e puxa a interpolação para o preto.
 *
 * 3. AS PARADAS DO FADE ESTÃO INVERTIDAS EM RELAÇÃO À REFERÊNCIA. Lá o fade é
 *    `transparent 0% -> background 75%` centrado em 50% 100%: transparente
 *    EMBAIXO, opaco EM CIMA — porque a função dele era mascarar o topo da
 *    FOTO. Nossos feixes moram no canto superior esquerdo; colar aquilo aqui
 *    apagaria os feixes e o componente renderizaria nada. Aqui as paradas são
 *    `background 0% -> background/0 62%`: opaco embaixo, dissolvendo para
 *    cima. Na diagonal até o canto superior esquerdo a distância normalizada
 *    dá 0.894 — bem além da parada de 62% — então os feixes ficam intactos.
 *    E não é decoração: é o que garante que gráfico, tabela e feed sejam
 *    lidos sobre --background chapado, não sobre uma névoa de luminância
 *    variável.
 *
 * 4. O FADE VEM DEPOIS DOS FEIXES, não antes. Na referência ele está em -z-10
 *    e os feixes em z-[2]; aqui é o último filho. Decorre direto de (3).
 *
 * 5. SEM `opacity-50` NO WRAPPER. A referência multiplica tudo por 0.5, então
 *    o alfa que você lê no arquivo não é o que a tela recebe. Os valores aqui
 *    já são finais — e some um contexto de empilhamento e uma camada de
 *    composição extras.
 *
 * 6. `contain-content`, NÃO `contain-strict`. `strict` = size+layout+paint+
 *    style. `paint` é o que queremos: recorta as caixas de 80rem giradas e
 *    deixa o compositor pular a camada fora de tela. `size` não compra nada
 *    aqui (fixed inset-0 já tira o tamanho dos insets) e só existe para
 *    morder quem depois puser um filho com dimensão. ATENÇÃO ao copiar esta
 *    classe: `paint` torna o elemento bloco contentor de descendente
 *    `position: fixed` — qualquer coisa fixed aninhada aqui dentro deixa de
 *    ser presa à viewport. Aqui não há nenhuma; num wrapper que envolvesse o
 *    SiteHeader, haveria.
 *
 * 7. `fixed`, NÃO `absolute` — mesma decisão deliberada do PlusBackground, por
 *    motivos novos: (a) o fade se ancora no fundo da PRÓPRIA caixa, e contra
 *    um documento de ~5000px os percentuais viram números sem sentido;
 *    (b) o wrapper do RootLayout não é `relative`, então `absolute inset-0`
 *    resolveria contra o bloco contentor inicial — tamanho de viewport que
 *    rola embora, o pior dos dois mundos; (c) caixa girada de 80rem em
 *    `absolute` entra na área de rolagem do documento e cria barra horizontal,
 *    coisa que `fixed` não faz.
 *
 * 8. NO MOBILE NÃO ESCONDEMOS — TROCAMOS. A referência usa `hidden lg:block`
 *    porque três feixes de 35rem girados a -45° dentro de 375px viram uma
 *    lavagem diagonal sem composição nenhuma (o problema é de desenho, não de
 *    custo: gradiente estático é uma pintura só e nada anima). Mas esconder
 *    devolve um retângulo preto chapado justo para a maioria das visitas.
 *    Então: um brilho de canto abaixo de `lg`, os três feixes a partir de
 *    `lg`. Mesmo token, mesmos alfas.
 *
 * 9. `[translate:5%_-50%]` AO LADO DE `-rotate-45` funciona igual em v3 e v4,
 *    apesar dos mecanismos diferentes: a v4 emite `rotate: -45deg` (propriedade
 *    individual) e a v3 emite `transform: translate(0,0) rotate(-45deg)`. Nos
 *    dois casos a propriedade nativa `translate` entra mais externa na matriz
 *    (translate × rotate × scale × transform), então a ordem de composição é a
 *    mesma. Nada a adaptar — está comentado porque PARECE que deveria quebrar.
 *
 * A cor é hsl(var(--feixe)), token novo em index.css: matiz da marca,
 * saturação derrubada. --primary a 75% de saturação num campo desse tamanho
 * não lê como luz, lê como fundo teal, e disputaria com text-primary e
 * bg-primary exatamente o mesmo sinal.
 *
 * Pico de alfa 0.08. Medido sobre --background (luminância relativa 0.00505),
 * o ponto mais claro do feixe compõe em 0.01484, e sobre ele:
 * text-muted-foreground = 5.76:1, text-foreground/70 = 7.4:1,
 * text-foreground/60 = 5.31:1. Todos acima de 4.5:1 com folga.
 */

/** Feixe largo. Os percentuais estranhos (68.54% / 55.02%) vêm da referência —
 *  são o que dá o corte assimétrico, e arredondar deixa o feixe simétrico
 *  demais, parecendo um borrão em vez de luz. */
const FEIXE_LARGO =
  "bg-[radial-gradient(68.54%_68.72%_at_55.02%_31.46%,hsl(var(--feixe)_/_0.08)_0%,hsl(var(--feixe)_/_0.02)_50%,hsl(var(--feixe)_/_0)_80%)]"

const FEIXE_MEDIO =
  "bg-[radial-gradient(50%_50%_at_50%_50%,hsl(var(--feixe)_/_0.06)_0%,hsl(var(--feixe)_/_0.02)_80%,hsl(var(--feixe)_/_0)_100%)]"

const FEIXE_FINO =
  "bg-[radial-gradient(50%_50%_at_50%_50%,hsl(var(--feixe)_/_0.04)_0%,hsl(var(--feixe)_/_0.02)_80%,hsl(var(--feixe)_/_0)_100%)]"

/** Versão de uma camada só para telas estreitas. Sem rotação: a -45° o feixe
 *  atravessa a tela inteira e deixa de ter direção. */
const BRILHO_MOBILE =
  "bg-[radial-gradient(50%_50%_at_50%_50%,hsl(var(--feixe)_/_0.07)_0%,hsl(var(--feixe)_/_0.02)_55%,hsl(var(--feixe)_/_0)_100%)]"

/** Fade inferior. Paradas invertidas em relação à referência — ver (3). */
const FADE_INFERIOR =
  "bg-[radial-gradient(125%_125%_at_50%_100%,hsl(var(--background))_0%,hsl(var(--background)_/_0)_62%)]"

export function BeamsBackground({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none fixed inset-0 -z-10 contain-content",
        className
      )}
    >
      {/* Abaixo de lg: um brilho de canto, sem rotação. */}
      <div
        className={cn(
          "absolute -left-32 -top-40 h-[38rem] w-[38rem] rounded-full lg:hidden",
          BRILHO_MOBILE
        )}
      />

      {/* lg+: os três feixes da referência. */}
      <div
        className={cn(
          "absolute left-0 top-0 hidden h-[80rem] w-[35rem] -translate-y-[350px] -rotate-45 rounded-full lg:block",
          FEIXE_LARGO
        )}
      />
      <div
        className={cn(
          "absolute left-0 top-0 hidden h-[80rem] w-56 -rotate-45 rounded-full [translate:5%_-50%] lg:block",
          FEIXE_MEDIO
        )}
      />
      <div
        className={cn(
          "absolute left-0 top-0 hidden h-[80rem] w-56 -translate-y-[350px] -rotate-45 lg:block",
          FEIXE_FINO
        )}
      />

      {/* Último filho de propósito: ele TEM que pintar por cima dos feixes. */}
      <div className={cn("absolute inset-0 size-full", FADE_INFERIOR)} />
    </div>
  )
}
