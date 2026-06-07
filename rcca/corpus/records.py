"""Frozen, JSON-serializable record types for the synthetic corpus.

These are plain data (no Django). Stable IDs make demos reproducible and every
record citable.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Spec:
    spec_id: str
    title: str
    clause: str  # invented clause number — the citation locator
    text: str
    requirement: str  # the measurable requirement


@dataclass(frozen=True)
class ProcessDataRow:
    row_id: str  # stable; the citation locator within a process-data table
    timestamp: str  # authored string, not real-time
    parameter: str
    value: float
    note: str = ""


@dataclass(frozen=True)
class ProcessData:
    source_id: str
    lot: str
    process: str
    rows: tuple[ProcessDataRow, ...]


@dataclass(frozen=True)
class PriorNC:
    nc_id: str
    title: str
    process: str
    defect_description: str
    root_cause: str  # documented (the NC is closed) — legitimately citable
    corrective_action: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class SampleNC:
    nc_id: str
    title: str
    part_number: str
    lot: str
    process: str
    defect_description: str
    spec_violated: str  # a Spec.spec_id
    measured_value: str
    required_value: str
    # The ANSWER KEY: the cause we planted so we can judge the agent. Test-only;
    # never returned by a tool, never fed to the agent.
    planted_root_cause: str
