import { useState, type ChangeEvent, type JSX } from "react";

// design.md §6.5: "operator inputs average cost per hour of unplanned
// downtime and average planned maintenance cost; the module outputs
// projected annual savings assuming a configurable reduction in unplanned
// downtime events." Entirely client-side — no backend endpoint needed.

function parseNonNegativeNumber(raw: string): number {
  const value = Number(raw);
  return Number.isFinite(value) && value >= 0 ? value : 0;
}

export function RoiEstimator(): JSX.Element {
  const [downtimeCostPerHour, setDowntimeCostPerHour] = useState(0);
  const [annualUnplannedHours, setAnnualUnplannedHours] = useState(0);
  const [annualMaintenanceCost, setAnnualMaintenanceCost] = useState(0);
  const [reductionPercent, setReductionPercent] = useState(30);

  const currentAnnualDowntimeCost = downtimeCostPerHour * annualUnplannedHours;
  const projectedSavings =
    currentAnnualDowntimeCost * (Math.min(100, Math.max(0, reductionPercent)) / 100) -
    annualMaintenanceCost;

  function handleNumberChange(setter: (value: number) => void) {
    return (event: ChangeEvent<HTMLInputElement>) => {
      setter(parseNonNegativeNumber(event.target.value));
    };
  }

  return (
    <section aria-label="ROI estimator">
      <h3>ROI Estimator</h3>
      <form
        onSubmit={(event) => {
          event.preventDefault();
        }}
      >
        <label>
          Downtime cost per hour (₹)
          <input
            type="number"
            min={0}
            value={downtimeCostPerHour}
            onChange={handleNumberChange(setDowntimeCostPerHour)}
          />
        </label>
        <label>
          Estimated unplanned downtime hours per year
          <input
            type="number"
            min={0}
            value={annualUnplannedHours}
            onChange={handleNumberChange(setAnnualUnplannedHours)}
          />
        </label>
        <label>
          Annual cost of running this monitoring system (₹)
          <input
            type="number"
            min={0}
            value={annualMaintenanceCost}
            onChange={handleNumberChange(setAnnualMaintenanceCost)}
          />
        </label>
        <label>
          Assumed reduction in unplanned downtime (%)
          <input
            type="number"
            min={0}
            max={100}
            value={reductionPercent}
            onChange={handleNumberChange(setReductionPercent)}
          />
        </label>
      </form>
      <dl>
        <dt>Current annual unplanned-downtime cost</dt>
        <dd>₹{currentAnnualDowntimeCost.toFixed(2)}</dd>
        <dt>Projected annual savings</dt>
        <dd>₹{projectedSavings.toFixed(2)}</dd>
      </dl>
    </section>
  );
}
