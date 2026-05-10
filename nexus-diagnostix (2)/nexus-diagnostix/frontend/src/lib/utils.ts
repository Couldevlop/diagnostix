import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combine intelligemment les classes Tailwind (déduplique, override ordonné).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Formate un montant en FCFA (Franc CFA).
 */
export function formatFcfa(amount: number): string {
  return new Intl.NumberFormat("fr-FR", {
    style: "decimal",
    maximumFractionDigits: 0,
  }).format(amount) + " FCFA";
}

/**
 * Formate un pourcentage avec 1 décimale.
 */
export function formatPercent(value: number): string {
  return `${value.toFixed(1)} %`;
}
