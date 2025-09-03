import { describe, it, expect } from "vitest";
import matchers from "@testing-library/jest-dom/matchers";
expect.extend(matchers);

import { render, screen } from "@testing-library/react";
import DashboardPage from "../app/dashboard/page";

describe("DashboardPage", () => {
  it("affiche le titre et le message d’accueil", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("dashboard-welcome")).toHaveTextContent("Bienvenue sur le cockpit.");
  });
});
