import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility to merge Tailwind classes safely.
 * clsx handles conditional classes, twMerge resolves conflicts
 * (e.g. "px-4 px-2" → "px-2").
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
