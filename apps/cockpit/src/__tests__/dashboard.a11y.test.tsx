import React from "react";
import { render, waitFor } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import DashboardPage from "@/app/dashboard/page";
import { Providers } from "@/components/Providers";

expect.extend(toHaveNoViolations);

describe("Dashboard", () => {
  beforeEach(() => {
    global.fetch = jest.fn((url: string): Promise<Response> => {
      if (url.includes("/api/agents")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              { date: "1", value: 1 },
              { date: "2", value: 2 },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      if (url.includes("/api/runs")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              { date: "1", p50: 1, p95: 2 },
              { date: "2", p50: 1, p95: 2 },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      if (url.includes("/api/feedbacks")) {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              { date: "1", positive: 1, neutral: 1, negative: 1 },
              { date: "2", positive: 2, neutral: 1, negative: 1 },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    });
  });

  it("n'a pas de violations d'accessibilité", async () => {
    const { container } = render(
      <Providers>
        <DashboardPage />
      </Providers>
    );
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
