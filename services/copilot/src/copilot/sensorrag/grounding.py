"""Numeric grounding checks for the SensorRAG faithfulness protocol
(design.md §6.4, §9, DD-030).

The literature survey backing this project identifies that no prior work
evaluates whether an SLM's *numeric* diagnostic claims are actually grounded
in retrieved structured sensor telemetry, as opposed to hallucinated
fluently from parametric memory (design.md DD-030). This module is a
heuristic implementation of that check: every number-shaped token in the
copilot's answer text is compared against every numeric value present in the
retrieved state objects, within a relative tolerance (to allow for the model
rounding a value differently than the raw JSON, e.g. "about 0.7" for
health_index=0.71).

What this does NOT catch (documented rather than silently assumed away):
a number that is genuinely present in the context but attributed to the
wrong claim (e.g. quoting the temperature as if it were the health index)
still counts as "grounded" here, since this checks presence, not semantic
attribution. A more rigorous protocol would need claim-level entity linking,
which is out of scope for this heuristic pass — see design.md §24.
"""

import re
from dataclasses import dataclass
from typing import Any

_NUMBER_PATTERN = re.compile(r"-?\d+\.?\d*")

_STATE_NUMERIC_FIELDS = ("health_index", "anomaly_score", "temperature_c")
_VIBRATION_NUMERIC_FIELDS = ("rms_g", "kurtosis", "crest_factor", "peak_to_peak_g")


@dataclass(frozen=True, slots=True)
class GroundingResult:
    total_numeric_claims: int
    ungrounded_claims: list[float]

    @property
    def is_fully_grounded(self) -> bool:
        return len(self.ungrounded_claims) == 0


def extract_numeric_claims(text: str) -> list[float]:
    """Every number-shaped substring in `text`, parsed as a float. Numbers
    embedded in ordinary words/IDs are an unavoidable false-positive source
    of this regex-based heuristic — see the module docstring.
    """
    claims = []
    for match in _NUMBER_PATTERN.findall(text):
        try:
            claims.append(float(match))
        except ValueError:
            continue
    return claims


def numeric_values_in_context(states: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for state in states:
        for key in _STATE_NUMERIC_FIELDS:
            value = state.get(key)
            if isinstance(value, int | float):
                values.append(float(value))
        vibration = state.get("vibration") or {}
        for key in _VIBRATION_NUMERIC_FIELDS:
            value = vibration.get(key)
            if isinstance(value, int | float):
                values.append(float(value))
    return values


def is_claim_grounded(
    claim: float, context_values: list[float], relative_tolerance: float = 0.02
) -> bool:
    for value in context_values:
        if value == 0:
            if abs(claim) < 1e-9:
                return True
            continue
        if abs(claim - value) / abs(value) <= relative_tolerance:
            return True
    return False


def check_numeric_grounding(answer: str, states: list[dict[str, Any]]) -> GroundingResult:
    context_values = numeric_values_in_context(states)
    claims = extract_numeric_claims(answer)
    ungrounded = [claim for claim in claims if not is_claim_grounded(claim, context_values)]
    return GroundingResult(total_numeric_claims=len(claims), ungrounded_claims=ungrounded)
