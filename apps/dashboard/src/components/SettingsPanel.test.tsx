import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SettingsPanel } from "./SettingsPanel";
import { DEFAULT_CONFIG } from "../config";

describe("SettingsPanel", () => {
  it("saves the Phase 2 toggle and thresholds", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<SettingsPanel config={DEFAULT_CONFIG} onSave={onSave} />);

    expect(screen.queryByLabelText(/health index alert threshold/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText(/enable phase 2/i));
    fireEvent.change(screen.getByLabelText(/health index alert threshold/i), {
      target: { value: "0.5" },
    });
    fireEvent.change(screen.getByLabelText(/temperature alert threshold/i), {
      target: { value: "65" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save settings/i }));

    expect(await screen.findByText(/settings saved/i)).toHaveTextContent(/make up/);
    expect(onSave).toHaveBeenCalledWith({
      ...DEFAULT_CONFIG,
      enablePhase2: true,
      alertHealthIndex: 0.5,
      alertTemperatureC: 65,
    });
  });

  it("shows the error when saving fails", async () => {
    const onSave = vi.fn().mockRejectedValue(new Error("HTTP 422"));
    render(<SettingsPanel config={DEFAULT_CONFIG} onSave={onSave} />);

    fireEvent.click(screen.getByRole("button", { name: /save settings/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("HTTP 422");
  });

  it("follows external config changes unless there are unsaved edits", () => {
    const onSave = vi.fn();
    const { rerender } = render(<SettingsPanel config={DEFAULT_CONFIG} onSave={onSave} />);

    rerender(<SettingsPanel config={{ ...DEFAULT_CONFIG, enablePhase2: true }} onSave={onSave} />);
    expect(screen.getByLabelText(/enable phase 2/i)).toBeChecked();

    fireEvent.change(screen.getByLabelText(/temperature alert threshold/i), {
      target: { value: "90" },
    });
    rerender(
      <SettingsPanel
        config={{ ...DEFAULT_CONFIG, enablePhase2: true, publishIntervalSeconds: 10 }}
        onSave={onSave}
      />,
    );
    expect(screen.getByLabelText(/temperature alert threshold/i)).toHaveValue(90);
    expect(screen.getByLabelText(/publish interval/i)).toHaveValue(5);
  });
});
