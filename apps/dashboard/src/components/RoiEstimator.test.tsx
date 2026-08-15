import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RoiEstimator } from "./RoiEstimator";

describe("RoiEstimator", () => {
  it("starts at zero cost/savings with the default inputs", () => {
    render(<RoiEstimator />);
    expect(screen.getByText(/current annual unplanned-downtime cost/i)).toBeInTheDocument();
    expect(screen.getAllByText("₹0.00")).toHaveLength(2);
  });

  it("computes projected savings from the entered inputs", () => {
    render(<RoiEstimator />);

    fireEvent.change(screen.getByLabelText(/downtime cost per hour/i), {
      target: { value: "1000" },
    });
    fireEvent.change(screen.getByLabelText(/unplanned downtime hours per year/i), {
      target: { value: "100" },
    });
    fireEvent.change(screen.getByLabelText(/annual cost of running this monitoring system/i), {
      target: { value: "5000" },
    });
    fireEvent.change(screen.getByLabelText(/assumed reduction/i), {
      target: { value: "50" },
    });

    // current annual downtime cost = 1000 * 100 = 100000
    expect(screen.getByText("₹100000.00")).toBeInTheDocument();
    // projected savings = 100000 * 0.5 - 5000 = 45000
    expect(screen.getByText("₹45000.00")).toBeInTheDocument();
  });

  it("ignores invalid (non-numeric) input rather than producing NaN", () => {
    render(<RoiEstimator />);

    fireEvent.change(screen.getByLabelText(/downtime cost per hour/i), {
      target: { value: "not-a-number" },
    });

    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();
  });
});
