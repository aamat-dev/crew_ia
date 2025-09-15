import { render, screen } from "@testing-library/react";
import DashboardPage from "../app/dashboard/page";
import { Providers } from "@/components/Providers";

describe("DashboardPage", () => {
  beforeEach(() => {
    global.fetch = jest.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    ) as jest.Mock;
  });

  it("affiche le titre et le message d’accueil", () => {
    render(
      <Providers>
        <DashboardPage />
      </Providers>
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("dashboard-welcome")).toHaveTextContent(
      "Bienvenue sur le cockpit.",
    );
  });
});
