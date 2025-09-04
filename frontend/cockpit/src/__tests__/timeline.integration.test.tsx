import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider, useMutation, useQueryClient } from "@tanstack/react-query";
import { ToastProvider, useToast } from "@/components/ds/Toast";

// composant de test simulant une timeline avec actions pause/reprise
function Timeline() {
  const qc = useQueryClient();
  const toast = useToast();
  const status = qc.getQueryData<string>(["status"]);

  const mutate = useMutation({
    // fonction de mutation fictive
    mutationFn: async (action: "pause" | "resume") => {
      return action;
    },
    onMutate: async (action) => {
      await qc.cancelQueries({ queryKey: ["status"] });
      const previous = qc.getQueryData(["status"]);
      qc.setQueryData(["status"], action === "pause" ? "paused" : "running");
      return { previous };
    },
    onError: (_err, _action, ctx) => {
      if (ctx?.previous) qc.setQueryData(["status"], ctx.previous);
    },
    onSuccess: () => {
      toast("Action réussie");
    },
  });

  return (
    <div>
      <span data-testid="status">{status}</span>
      <button onClick={() => mutate.mutate("pause")}>Pause</button>
      <button onClick={() => mutate.mutate("resume")}>Resume</button>
    </div>
  );
}

describe("Timeline", () => {
  it("affiche des toasts et met à jour le statut de façon optimiste", async () => {
    const client = new QueryClient();
    client.setQueryData(["status"], "running");

    render(
      <QueryClientProvider client={client}>
        <ToastProvider>
          <Timeline />
        </ToastProvider>
      </QueryClientProvider>
    );

    expect(screen.getByTestId("status")).toHaveTextContent("running");

    fireEvent.click(screen.getByText("Pause"));
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("paused"));
    await screen.findByRole("alert");

    fireEvent.click(screen.getByText("Resume"));
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("running"));
    const alerts = await screen.findAllByRole("alert");
    expect(alerts).toHaveLength(2);
  });
});

