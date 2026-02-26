import { expect, test } from "@playwright/test";

test("traversing main tabs emits zero console errors", async ({ page }) => {
  const errors = [];

  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(`console: ${message.text()}`);
    }
  });

  page.on("pageerror", (error) => {
    errors.push(`pageerror: ${error.message}`);
  });

  await page.goto("/");
  await page.waitForLoadState("networkidle");

  await expect(page.getByRole("tab", { name: "OVERVIEW" })).toBeVisible();
  await expect(page.getByText("COGNITIVE LOOP")).toBeVisible();

  await page.getByRole("tab", { name: "AGENTS" }).click();
  await expect(page.getByText("ORCHESTRATION TOPOLOGY")).toBeVisible();

  await page.getByRole("tab", { name: "MEMORY" }).click();
  await expect(page.getByText("TEMPORAL KNOWLEDGE GRAPH")).toBeVisible();

  await page.getByRole("tab", { name: "DECISIONS" }).click();
  await expect(page.getByText("DEFERRAL MODULE")).toBeVisible();

  await page.getByRole("tab", { name: "OVERVIEW" }).click();
  await expect(page.getByText("PERFORMANCE STREAM")).toBeVisible();

  expect(errors, `Unexpected console/page errors:\n${errors.join("\n")}`).toEqual([]);
});
