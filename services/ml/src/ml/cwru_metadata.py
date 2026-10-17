"""CWRU Bearing Data Center file catalog (design.md §6.3, §24).

Maps every file in the Normal Baseline + 12kHz Drive-End Fault Data sets
(the standard benchmark subset used throughout the CWRU literature) to its
download URL and decoded condition. Scraped directly from the live pages at
https://engineering.case.edu/bearingdatacenter/normal-baseline-data and
.../12k-drive-end-bearing-fault-data (2026-09-18) — each dict key is the
exact label the site itself uses next to that file's download link, so this
table can be re-verified by diffing against the live page rather than trusted
from memory (CWRU file-number-to-condition tables are a common source of
transcription errors in third-party tutorials).

Label grammar: "Normal_<load>", "IR<diameter>_<load>", "B<diameter>_<load>",
"OR<diameter>@<clock_position>_<load>" — diameter in thousandths of an inch
(007 = 0.007"), load in horsepower (0-3), clock position is the outer-race
defect's position relative to the load zone (6/3/12 o'clock; not every
diameter has all three, matching the site's own asterisked gaps).
"""

import re
from dataclasses import dataclass
from typing import Literal

FaultType = Literal["normal", "inner_race", "ball", "outer_race"]

# label -> download URL, scraped verbatim from the CWRU Bearing Data Center.
CWRU_FILES: dict[str, str] = {
    "Normal_0": "https://engineering.case.edu/sites/default/files/97.mat",
    "Normal_1": "https://engineering.case.edu/sites/default/files/98.mat",
    "Normal_2": "https://engineering.case.edu/sites/default/files/99.mat",
    "Normal_3": "https://engineering.case.edu/sites/default/files/100.mat",
    "IR007_0": "https://engineering.case.edu/sites/default/files/105.mat",
    "IR007_1": "https://engineering.case.edu/sites/default/files/106.mat",
    "IR007_2": "https://engineering.case.edu/sites/default/files/107.mat",
    "IR007_3": "https://engineering.case.edu/sites/default/files/108.mat",
    "B007_0": "https://engineering.case.edu/sites/default/files/118.mat",
    "B007_1": "https://engineering.case.edu/sites/default/files/119.mat",
    "B007_2": "https://engineering.case.edu/sites/default/files/120.mat",
    "B007_3": "https://engineering.case.edu/sites/default/files/121.mat",
    "OR007@6_0": "https://engineering.case.edu/sites/default/files/130.mat",
    "OR007@6_1": "https://engineering.case.edu/sites/default/files/131.mat",
    "OR007@6_2": "https://engineering.case.edu/sites/default/files/132.mat",
    "OR007@6_3": "https://engineering.case.edu/sites/default/files/133.mat",
    "OR007@3_0": "https://engineering.case.edu/sites/default/files/144.mat",
    "OR007@3_1": "https://engineering.case.edu/sites/default/files/145.mat",
    "OR007@3_2": "https://engineering.case.edu/sites/default/files/146.mat",
    "OR007@3_3": "https://engineering.case.edu/sites/default/files/147.mat",
    "OR007@12_0": "https://engineering.case.edu/sites/default/files/156.mat",
    "OR007@12_1": "https://engineering.case.edu/sites/default/files/158.mat",
    "OR007@12_2": "https://engineering.case.edu/sites/default/files/159.mat",
    "OR007@12_3": "https://engineering.case.edu/sites/default/files/160.mat",
    "IR014_0": "https://engineering.case.edu/sites/default/files/169.mat",
    "IR014_1": "https://engineering.case.edu/sites/default/files/170.mat",
    "IR014_2": "https://engineering.case.edu/sites/default/files/171.mat",
    "IR014_3": "https://engineering.case.edu/sites/default/files/172.mat",
    "B014_0": "https://engineering.case.edu/sites/default/files/185.mat",
    "B014_1": "https://engineering.case.edu/sites/default/files/186.mat",
    "B014_2": "https://engineering.case.edu/sites/default/files/187.mat",
    "B014_3": "https://engineering.case.edu/sites/default/files/188.mat",
    "OR014@6_0": "https://engineering.case.edu/sites/default/files/197.mat",
    "OR014@6_1": "https://engineering.case.edu/sites/default/files/198.mat",
    "OR014@6_2": "https://engineering.case.edu/sites/default/files/199.mat",
    "OR014@6_3": "https://engineering.case.edu/sites/default/files/200.mat",
    "IR021_0": "https://engineering.case.edu/sites/default/files/209.mat",
    "IR021_1": "https://engineering.case.edu/sites/default/files/210.mat",
    "IR021_2": "https://engineering.case.edu/sites/default/files/211.mat",
    "IR021_3": "https://engineering.case.edu/sites/default/files/212.mat",
    "B021_0": "https://engineering.case.edu/sites/default/files/222.mat",
    "B021_1": "https://engineering.case.edu/sites/default/files/223.mat",
    "B021_2": "https://engineering.case.edu/sites/default/files/224.mat",
    "B021_3": "https://engineering.case.edu/sites/default/files/225.mat",
    "OR021@6_0": "https://engineering.case.edu/sites/default/files/234.mat",
    "OR021@6_1": "https://engineering.case.edu/sites/default/files/235.mat",
    "OR021@6_2": "https://engineering.case.edu/sites/default/files/236.mat",
    "OR021@6_3": "https://engineering.case.edu/sites/default/files/237.mat",
    "OR021@3_0": "https://engineering.case.edu/sites/default/files/246.mat",
    "OR021@3_1": "https://engineering.case.edu/sites/default/files/247.mat",
    "OR021@3_2": "https://engineering.case.edu/sites/default/files/248.mat",
    "OR021@3_3": "https://engineering.case.edu/sites/default/files/249.mat",
    "OR021@12_0": "https://engineering.case.edu/sites/default/files/258.mat",
    "OR021@12_1": "https://engineering.case.edu/sites/default/files/259.mat",
    "OR021@12_2": "https://engineering.case.edu/sites/default/files/260.mat",
    "OR021@12_3": "https://engineering.case.edu/sites/default/files/261.mat",
    "IR028_0": "https://engineering.case.edu/sites/default/files/3001.mat",
    "IR028_1": "https://engineering.case.edu/sites/default/files/3002.mat",
    "IR028_2": "https://engineering.case.edu/sites/default/files/3003.mat",
    "IR028_3": "https://engineering.case.edu/sites/default/files/3004.mat",
    "B028_0": "https://engineering.case.edu/sites/default/files/3005.mat",
    "B028_1": "https://engineering.case.edu/sites/default/files/3006.mat",
    "B028_2": "https://engineering.case.edu/sites/default/files/3007.mat",
    "B028_3": "https://engineering.case.edu/sites/default/files/3008.mat",
}

_LABEL_RE = re.compile(r"^(Normal|IR|B|OR)(\d{3})?(?:@(\d+))?_(\d)$")


@dataclass(frozen=True, slots=True)
class CwruFileInfo:
    label: str
    url: str
    fault_type: FaultType
    load_hp: int
    fault_diameter_in: float | None
    outer_race_position: int | None


def _decode_label(label: str) -> CwruFileInfo:
    match = _LABEL_RE.match(label)
    if not match:
        raise ValueError(f"Unrecognized CWRU label format: {label!r}")
    kind, diameter_thousandths, or_position, load = match.groups()

    kind_to_fault_type: dict[str, FaultType] = {
        "Normal": "normal",
        "IR": "inner_race",
        "B": "ball",
        "OR": "outer_race",
    }
    fault_type = kind_to_fault_type[kind]

    return CwruFileInfo(
        label=label,
        url=CWRU_FILES[label],
        fault_type=fault_type,
        load_hp=int(load),
        fault_diameter_in=int(diameter_thousandths) / 1000 if diameter_thousandths else None,
        outer_race_position=int(or_position) if or_position else None,
    )


CWRU_FILE_INFO: dict[str, CwruFileInfo] = {label: _decode_label(label) for label in CWRU_FILES}
