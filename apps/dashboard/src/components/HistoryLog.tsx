import { useState, type JSX } from "react";
import type { DigitalTwinState } from "../api";

// design.md §6.5: "Historical log: last 24 hours of state objects, filterable
// by alert level." The underlying `GET /state/history` endpoint caps at 1000
// rows (services/api/src/api/main.py `Query(le=1000)`), so at the edge's
// default 5s publish interval this covers roughly the most recent ~83
// minutes, not a true 24h window — tracked as a known gap (design.md §26)
// rather than silently claimed as 24h.

const ALERT_LEVELS = ["all", "normal", "warning", "critical"] as const;
type AlertLevelFilter = (typeof ALERT_LEVELS)[number];

interface HistoryLogProps {
  /** Most-recent-first, as returned by the api. */
  history: DigitalTwinState[];
}

export function HistoryLog({ history }: HistoryLogProps): JSX.Element {
  const [filter, setFilter] = useState<AlertLevelFilter>("all");

  const filtered =
    filter === "all" ? history : history.filter((s) => (s.alert_level ?? "normal") === filter);

  return (
    <section aria-label="Historical log">
      <h3>Historical Log</h3>
      <label>
        Filter by alert level
        <select
          value={filter}
          onChange={(event) => {
            setFilter(event.target.value as AlertLevelFilter);
          }}
        >
          {ALERT_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </select>
      </label>
      {filtered.length === 0 ? (
        <p>No readings match this filter.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th scope="col">Timestamp</th>
              <th scope="col">Vibration RMS (g)</th>
              <th scope="col">Temperature (°C)</th>
              <th scope="col">Health index</th>
              <th scope="col">Alert level</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr key={s.timestamp}>
                <td>{s.timestamp}</td>
                <td>{s.vibration.rms_g}</td>
                <td>{s.temperature_c}</td>
                <td>{s.health_index ?? "—"}</td>
                <td>{s.alert_level ?? "normal"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
