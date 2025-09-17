import { render, screen } from "@testing-library/react";
import DashboardPage from "../app/dashboard/page";
import { Providers } from "@/components/Providers";

describe("DashboardPage", () => {
  it("affiche le titre et la section timeline", () => {
    render(
      <Providers>
        <DashboardPage />
      </Providers>
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Derniers runs")).toBeInTheDocument();
  });
});
