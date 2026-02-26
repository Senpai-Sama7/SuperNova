import { describe, expect, it } from "vitest";
import { clamp, toFiniteNumber } from "./numberGuards";

describe("toFiniteNumber", () => {
  it("returns finite numeric input", () => {
    expect(toFiniteNumber(4.2, 0)).toBe(4.2);
    expect(toFiniteNumber("7.5", 0)).toBe(7.5);
  });

  it("returns fallback for invalid values", () => {
    expect(toFiniteNumber(undefined, 0.5)).toBe(0.5);
    expect(toFiniteNumber("not-a-number", 3)).toBe(3);
    expect(toFiniteNumber(Infinity, 2)).toBe(2);
    expect(toFiniteNumber(-Infinity, 2)).toBe(2);
  });
});

describe("clamp", () => {
  it("keeps values inside bounds", () => {
    expect(clamp(0.6, 0, 1)).toBe(0.6);
  });

  it("clamps values below and above bounds", () => {
    expect(clamp(-0.2, 0, 1)).toBe(0);
    expect(clamp(1.5, 0, 1)).toBe(1);
  });

  it("works with toFiniteNumber for NaN-safe pipelines", () => {
    const safe = clamp(toFiniteNumber(undefined, 0.5), 0, 1);
    expect(safe).toBe(0.5);
  });
});
