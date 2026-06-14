import { describe, expect, it } from "vitest";
import { compactObject, titleCase } from "@/lib/utils";

describe("utils", () => {
  it("removes empty query values", () => {
    expect(compactObject({ status: "OPEN", search: "", page: 1, client: null })).toEqual({
      status: "OPEN",
      page: 1,
    });
  });

  it("formats enum-like strings for labels", () => {
    expect(titleCase("IN_PROGRESS")).toBe("In Progress");
  });
});

