import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TrendChart } from "./TrendChart";

describe("TrendChart", () => {
  it("shows a no-data message when points is empty", () => {
    render(<TrendChart label="Vibration RMS" unit="g" points={[]} />);
    expect(screen.getByText(/no trend data yet/i)).toBeInTheDocument();
  });

  it("renders a chart with the latest value and reading count", () => {
    render(<TrendChart label="Vibration RMS" unit="g" points={[0.1, 0.2, 0.42]} />);
    expect(screen.getByText(/0\.42 g/)).toBeInTheDocument();
    expect(screen.getByText(/last 3 readings/)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Vibration RMS trend chart/ })).toBeInTheDocument();
  });

  it("uses singular wording for a single reading", () => {
    render(<TrendChart label="Temperature" unit="°C" points={[45]} />);
    expect(screen.getByText(/last 1 reading\)/)).toBeInTheDocument();
  });
});
