import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/** Junta classes condicionais (clsx) e resolve conflitos do Tailwind
 *  (twMerge), para que uma classe passada por prop vença a padrão do
 *  componente em vez das duas saírem no HTML brigando. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
