import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HealthGauge } from "./HealthGauge";

describe("HealthGauge", () => {
  it("shows a not-available message when health index is null", () => {
    render(<HealthGauge healthIndex={null} />);
    expect(screen.getByText(/not available yet/i)).toBeInTheDocument();
  });

  it("renders the gauge with the formatted value when health index is present", () => {
    render(<HealthGauge healthIndex={0.88} />);
    expect(screen.getByRole("img", { name: /0\.88/ })).toBeInTheDocument();
  });

  it("clamps out-of-range values into [0, 1]", () => {
    render(<HealthGauge healthIndex={1.5} />);
    expect(screen.getByRole("img", { name: /1\.00/ })).toBeInTheDocument();
  });
});
