import React from "react";
import { render, screen } from "@testing-library/react";
import { AppShell } from "@/components/shell/AppShell";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/dashboard",
}));

describe("Sidebar (AppShell)", () => {
  it("rend la navigation avec libellés visibles", () => {
    render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );
    const nav = screen.getByRole("navigation", { name: /navigation principale/i });
    expect(nav).toBeInTheDocument();
    expect(screen.getByText(/aperçu/i)).toBeInTheDocument();
    expect(screen.getByText(/runs/i)).toBeInTheDocument();
    expect(screen.getByText(/réglages/i)).toBeInTheDocument();
  });
});

