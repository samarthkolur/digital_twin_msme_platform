"""Training pipeline entry points.

Model implementations (Isolation Forest baseline, 1D conv autoencoder) land
in Phase 4 per design.md §6.3 / §10. This module currently only proves the
package, dependency set, and test/type-check tooling wire up correctly.
"""


def pipeline_version() -> str:
    return "0.1.0"
