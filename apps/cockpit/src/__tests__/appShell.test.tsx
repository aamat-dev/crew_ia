import React from "react";
import { render } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { AppShell } from "@/components/shell/AppShell";
import { KpiCard } from "@/components/ds/KpiCard";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/",
}));

expect.extend(toHaveNoViolations);

describe("AppShell", () => {
  it("n'a pas de violations d'accessibilité", async () => {
    const { container } = render(
      <AppShell>
        <KpiCard title="Test" value="42" />
      </AppShell>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
