import { describe, expect, it } from "vitest";
import { Basis, BitValue, ProtocolType } from "../src/domain";

describe("Domain types", () => {
  it("should have correct basis values", () => {
    expect(Basis.Rectilinear).toBe("rectilinear");
    expect(Basis.Diagonal).toBe("diagonal");
  });

  it("should have correct bit values", () => {
    expect(BitValue.Zero).toBe(0);
    expect(BitValue.One).toBe(1);
  });

  it("should list all protocol types", () => {
    const protocols = Object.values(ProtocolType);
    expect(protocols).toHaveLength(5);
    expect(protocols).toContain("bb84");
    expect(protocols).toContain("e91");
    expect(protocols).toContain("b92");
    expect(protocols).toContain("sarg04");
    expect(protocols).toContain("decoy_bb84");
  });
});
