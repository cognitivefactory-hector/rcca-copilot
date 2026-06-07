"""Synthetic corpus — fictional NCs, process data, specs, and prior NCs."""
from .data import DISCLAIMER, PRIOR_NCS, PROCESS_DATA, SAMPLE_NCS, SPECS
from .records import PriorNC, ProcessData, ProcessDataRow, SampleNC, Spec

__all__ = [
    "DISCLAIMER",
    "PRIOR_NCS",
    "PROCESS_DATA",
    "SAMPLE_NCS",
    "SPECS",
    "PriorNC",
    "ProcessData",
    "ProcessDataRow",
    "SampleNC",
    "Spec",
]
