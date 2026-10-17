// Mirrors `services/copilot/src/copilot/main.py`'s QueryResponseBody.
export interface CopilotAnswer {
  answer: string;
  used_fallback: boolean;
  context_size: number;
}

const COPILOT_URL = import.meta.env.VITE_COPILOT_URL;

export async function askCopilot(query: string): Promise<CopilotAnswer> {
  let response: Response;
  try {
    response = await fetch(`${COPILOT_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
  } catch {
    // The copilot container only runs with the "phase2" Compose profile, so
    // enabling Phase 2 from the dashboard alone does not start it (DD-047).
    throw new Error(
      "The copilot service isn't running. Start the Phase 2 services with `make up`.",
    );
  }
  if (response.status === 503) {
    throw new Error("The copilot is turned off (Phase 2 is disabled).");
  }
  if (!response.ok) {
    throw new Error(`Copilot request failed: HTTP ${String(response.status)}`);
  }
  return (await response.json()) as CopilotAnswer;
}
