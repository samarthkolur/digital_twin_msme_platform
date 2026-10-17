import { useState, type JSX, type SubmitEvent } from "react";
import { askCopilot, type CopilotAnswer } from "../copilot";

/** Phase 2: natural-language questions about the machine (design.md §6.4). */
export function CopilotPanel(): JSX.Element {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<
    | { kind: "idle" }
    | { kind: "asking" }
    | { kind: "answered"; answer: CopilotAnswer }
    | { kind: "error"; message: string }
  >({ kind: "idle" });

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (query.trim() === "") return;
    setResult({ kind: "asking" });
    try {
      setResult({ kind: "answered", answer: await askCopilot(query) });
    } catch (err) {
      setResult({
        kind: "error",
        message: err instanceof Error ? err.message : "Could not reach the copilot",
      });
    }
  }

  return (
    <section aria-label="Copilot">
      <h3>Ask the Copilot</h3>
      <form onSubmit={(event) => void handleSubmit(event)}>
        <label>
          Question
          <input
            type="text"
            value={query}
            placeholder="Is the motor running normally?"
            onChange={(event) => {
              setQuery(event.target.value);
            }}
          />
        </label>
        <button type="submit" disabled={result.kind === "asking"}>
          Ask
        </button>
      </form>
      {result.kind === "answered" && (
        <p>
          {result.answer.answer}
          {result.answer.used_fallback && " (rule-based fallback)"}
        </p>
      )}
      {result.kind === "error" && <p role="alert">{result.message}</p>}
    </section>
  );
}
