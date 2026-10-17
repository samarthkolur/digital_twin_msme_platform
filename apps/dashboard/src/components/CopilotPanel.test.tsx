import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CopilotPanel } from "./CopilotPanel";
import { askCopilot } from "../copilot";

vi.mock("../copilot", () => ({ askCopilot: vi.fn() }));
const mockedAsk = vi.mocked(askCopilot);

function ask(question: string): void {
  fireEvent.change(screen.getByLabelText(/question/i), { target: { value: question } });
  fireEvent.click(screen.getByRole("button", { name: /ask/i }));
}

describe("CopilotPanel", () => {
  beforeEach(() => {
    mockedAsk.mockReset();
  });

  it("shows the copilot's answer", async () => {
    mockedAsk.mockResolvedValue({
      answer: "Running normally.",
      used_fallback: true,
      context_size: 3,
    });
    render(<CopilotPanel />);

    ask("Is it okay?");

    expect(
      await screen.findByText(/running normally\. \(rule-based fallback\)/i),
    ).toBeInTheDocument();
    expect(mockedAsk).toHaveBeenCalledWith("Is it okay?");
  });

  it("shows the error when the copilot refuses", async () => {
    mockedAsk.mockRejectedValue(new Error("The copilot is turned off (Phase 2 is disabled)."));
    render(<CopilotPanel />);

    ask("Is it okay?");

    expect(await screen.findByRole("alert")).toHaveTextContent(/phase 2 is disabled/i);
  });

  it("ignores an empty question", () => {
    render(<CopilotPanel />);
    ask("   ");
    expect(mockedAsk).not.toHaveBeenCalled();
  });
});
