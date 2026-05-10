import { describe, it, expect } from "vitest";
import { cn, formatFcfa, formatPercent } from "@/lib/utils";

describe("cn", () => {
  it("combine plusieurs classes", () => {
    expect(cn("px-2", "py-3")).toBe("px-2 py-3");
  });

  it("déduplique et override les classes Tailwind conflictuelles", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });

  it("ignore les valeurs falsy", () => {
    expect(cn("a", false, null, undefined, "b")).toBe("a b");
  });
});

describe("formatFcfa", () => {
  it("formate les montants en FCFA avec séparateurs", () => {
    expect(formatFcfa(1500000)).toMatch(/1\s?500\s?000\s?FCFA/);
  });

  it("gère le zéro", () => {
    expect(formatFcfa(0)).toMatch(/^0\s?FCFA$/);
  });

  it("ne montre pas de décimales", () => {
    expect(formatFcfa(1234.56)).not.toContain(",");
  });
});

describe("formatPercent", () => {
  it("formate avec 1 décimale", () => {
    expect(formatPercent(45.678)).toBe("45.7 %");
  });

  it("gère le zéro", () => {
    expect(formatPercent(0)).toBe("0.0 %");
  });

  it("gère 100 %", () => {
    expect(formatPercent(100)).toBe("100.0 %");
  });
});
