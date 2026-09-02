/** Helpers de formatação. Ficam fora dos componentes para não quebrar o fast
 *  refresh do Vite, que só funciona quando um arquivo exporta apenas
 *  componentes. */

/** "2026-09-02" -> "02 set". Evita o eixo virar uma parede de ISO. */
export function formatarData(iso: string): string {
  const d = new Date(`${iso}T12:00:00`)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" }).replace(".", "")
}

/** Distância em linguagem natural a partir de um instante de referência
 *  RECEBIDO, não de Date.now(): ler o relógio durante o render torna o
 *  resultado instável entre renders e é o que o lint aponta como impureza. */
export function haQuantoTempo(iso: string, agora: number): string {
  const horas = (agora - new Date(iso).getTime()) / 36e5
  if (horas < 1) return "agora há pouco"
  if (horas < 24) return `há ${Math.round(horas)} h`
  return `há ${Math.round(horas / 24)} d`
}
