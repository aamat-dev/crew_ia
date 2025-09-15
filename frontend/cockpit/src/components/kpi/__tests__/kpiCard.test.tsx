import React from "react";
import { render, screen } from "@testing-library/react";
import { KpiCard } from "../KpiCard";

describe("KpiCard", () => {
  it("affiche un skeleton en chargement", () => {
    render(<KpiCard title="Total runs" loading variant="glass" />);
    expect(screen.getByRole("group")).toHaveAttribute("aria-busy", "true");
    // Deux placeholders de statut (valeur + sous-texte)
    const statuses = screen.getAllByRole("status");
    expect(statuses.length).toBeGreaterThanOrEqual(1);
  });

  it("affiche un état aucune donnée", () => {
    render(<KpiCard title="Total runs" noData />);
    expect(screen.getByRole("group")).toHaveAccessibleName(/aucune donnée/i);
    expect(screen.getByText(/Aucune donnée/i)).toBeInTheDocument();
  });

  it("affiche le titre et la valeur", () => {
    render(<KpiCard title="Total runs" value={12} />);
    expect(screen.getByText("Total runs")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("affiche la variation négative (delta)", () => {
    render(<KpiCard title="Taux d'erreur" value={3} delta={-5} />);
    expect(screen.getByText('5%')).toBeInTheDocument();
  });

  it("affiche l'unité jointe à la valeur", () => {
    render(<KpiCard title="Satisfaction" value={95} unit="%" />);
    expect(screen.getByText('95')).toBeInTheDocument();
    // l'unité est dans un span séparé
    expect(screen.getByText('%')).toBeInTheDocument();
  });
});
