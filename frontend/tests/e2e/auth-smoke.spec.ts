import { expect, test } from "@playwright/test";

test("owner can log in and reach dashboard", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  await page.locator('input[name="email"]').fill("owner@techcare.test");
  await page.locator('input[name="password"]').fill("Test@12345");
  await page.getByRole("button", { name: /open workspace/i }).click();
  await expect(page.getByRole("heading", { name: "Service operations at a glance" })).toBeVisible();
});
