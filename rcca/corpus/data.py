"""The authored synthetic corpus — fictional, no employer data, ever.

Stable IDs throughout so demos are reproducible. The agent reaches this data
only through the tools in rcca/agent/tools.py.
"""
from .records import PriorNC, ProcessData, ProcessDataRow, SampleNC, Spec

DISCLAIMER = (
    "Simulated data for demonstration only. Entirely fictional — not affiliated "
    "with any employer and not derived from any real nonconformance, process, "
    "or specification."
)

# --- Specifications ---------------------------------------------------------

SPECS: dict[str, Spec] = {
    "SPEC-AN-7": Spec(
        spec_id="SPEC-AN-7",
        title="Type II Sulfuric Anodize — Coating Thickness",
        clause="§4.2",
        text=(
            "Anodic coating thickness shall be measured per eddy-current method "
            "at five points and shall fall within the specified range for all points."
        ),
        requirement="Coating thickness 0.7–1.2 mil (all measured points).",
    ),
    "SPEC-PL-3": Spec(
        spec_id="SPEC-PL-3",
        title="Electroless Nickel Plating — Adhesion",
        clause="§3.5",
        text=(
            "Plated deposits shall exhibit no separation from the basis metal when "
            "subjected to the bend-to-fracture adhesion test."
        ),
        requirement="No lifting, peeling, or flaking after bend-to-fracture test.",
    ),
    "SPEC-ET-2": Spec(
        spec_id="SPEC-ET-2",
        title="Chemical Etch — Slot Dimensional Control",
        clause="§2.1",
        text=(
            "Etched slot width shall be held within tolerance, measured optically "
            "at three stations along the slot length."
        ),
        requirement="Slot width 0.50 ± 0.02 mm.",
    ),
    "SPEC-DIM-1": Spec(
        spec_id="SPEC-DIM-1",
        title="Machined Bore — Diameter",
        clause="§6.0",
        text="Finished bore diameter shall be within tolerance after final machining.",
        requirement="Bore diameter 12.00 ± 0.03 mm.",
    ),
}

# --- Process data (per lot) -------------------------------------------------

PROCESS_DATA: dict[str, ProcessData] = {
    # Anodize: bath voltage sags mid-run -> current density drops -> thin coating.
    "LOT-AN-42": ProcessData(
        source_id="PD-LOT-AN-42",
        lot="LOT-AN-42",
        process="Type II sulfuric anodize",
        rows=(
            ProcessDataRow("PD-AN-42-01", "T+00:00", "bath_voltage_V", 15.0, "at setpoint"),
            ProcessDataRow("PD-AN-42-02", "T+05:00", "bath_voltage_V", 14.8, ""),
            ProcessDataRow("PD-AN-42-03", "T+10:00", "bath_voltage_V", 11.3, "below setpoint"),
            ProcessDataRow("PD-AN-42-04", "T+15:00", "bath_voltage_V", 11.1, "below setpoint"),
            ProcessDataRow("PD-AN-42-05", "T+20:00", "bath_voltage_V", 14.9, "recovered"),
            ProcessDataRow("PD-AN-42-06", "T+05:00", "current_density_asf", 11.8, ""),
            ProcessDataRow("PD-AN-42-07", "T+12:00", "current_density_asf", 7.9, "low"),
            ProcessDataRow("PD-AN-42-08", "final", "coating_thickness_mil", 0.4, "below floor"),
            ProcessDataRow("PD-AN-42-09", "final", "bath_temp_F", 70.0, "in range"),
        ),
    ),
    # Plating: activation dwell far short of process window -> weak adhesion.
    "LOT-PL-17": ProcessData(
        source_id="PD-LOT-PL-17",
        lot="LOT-PL-17",
        process="Electroless nickel plating",
        rows=(
            ProcessDataRow(
                "PD-PL-17-01", "step:activation", "activation_dwell_s", 18.0, "spec 60-90 s"
            ),
            ProcessDataRow("PD-PL-17-02", "step:plate", "bath_temp_C", 88.0, "in range"),
            ProcessDataRow("PD-PL-17-03", "step:plate", "bath_pH", 4.8, "in range"),
            ProcessDataRow("PD-PL-17-04", "step:plate", "deposit_thickness_um", 12.5, "in range"),
            ProcessDataRow("PD-PL-17-05", "test", "adhesion_bend", 0.0, "failed: peeling observed"),
        ),
    ),
    # Etch: bath temperature elevated -> faster etch rate -> slot over-cut.
    "LOT-ET-09": ProcessData(
        source_id="PD-LOT-ET-09",
        lot="LOT-ET-09",
        process="Chemical etch",
        rows=(
            ProcessDataRow("PD-ET-09-01", "T+00:00", "etch_bath_temp_C", 32.4, "spec 24-26 C"),
            ProcessDataRow("PD-ET-09-02", "T+02:00", "etch_bath_temp_C", 32.1, "above range"),
            ProcessDataRow("PD-ET-09-03", "run", "etch_time_s", 120.0, "nominal"),
            ProcessDataRow("PD-ET-09-04", "measure", "slot_width_mm", 0.56, "over high limit"),
        ),
    ),
    # Thin-evidence case: everything reads near-nominal; data gives no clear cause.
    "LOT-MX-55": ProcessData(
        source_id="PD-LOT-MX-55",
        lot="LOT-MX-55",
        process="CNC milling",
        rows=(
            ProcessDataRow("PD-MX-55-01", "part:03", "bore_dia_mm", 12.01, "in tolerance"),
            ProcessDataRow("PD-MX-55-02", "part:07", "bore_dia_mm", 11.99, "in tolerance"),
            ProcessDataRow("PD-MX-55-03", "part:11", "bore_dia_mm", 12.04, "marginal over"),
            ProcessDataRow("PD-MX-55-04", "run", "spindle_rpm", 8000.0, "nominal"),
            ProcessDataRow("PD-MX-55-05", "run", "coolant_temp_C", 21.0, "nominal"),
        ),
    ),
}

# --- Prior (closed) nonconformances — for recurrence search -----------------

PRIOR_NCS: tuple[PriorNC, ...] = (
    PriorNC(
        nc_id="NC-PRIOR-101",
        title="Anodize coating thin on aluminum brackets",
        process="Type II sulfuric anodize",
        defect_description="Coating thickness below the lower limit on several parts in the lot.",
        root_cause=(
            "Rectifier B output sagged during the run, lowering current density and "
            "starving coating growth."
        ),
        corrective_action=(
            "Added per-run rectifier output verification; replaced aging rectifier contactor."
        ),
        keywords=("anodize", "coating", "thickness", "voltage", "rectifier", "current density"),
    ),
    PriorNC(
        nc_id="NC-PRIOR-102",
        title="Electroless nickel peeling after bend test",
        process="Electroless nickel plating",
        defect_description="Deposit lifted from basis metal during adhesion testing.",
        root_cause=(
            "Activation step cut short during a manual line run, leaving the surface "
            "under-activated."
        ),
        corrective_action="Added a timed interlock on the activation tank; operator re-training.",
        keywords=("plating", "nickel", "adhesion", "peeling", "activation", "pre-clean"),
    ),
    PriorNC(
        nc_id="NC-PRIOR-103",
        title="Etched slots oversized on RF housings",
        process="Chemical etch",
        defect_description="Slot width exceeded the upper tolerance across the panel.",
        root_cause="Etch bath ran hot after a chiller fault, accelerating the etch rate.",
        corrective_action="Tied a temperature interlock to the etch timer; added chiller alarm.",
        keywords=("etch", "slot", "over-cut", "oversized", "temperature", "bath"),
    ),
    PriorNC(
        nc_id="NC-PRIOR-104",
        title="Passivation staining on stainless fittings",
        process="Citric passivation",
        defect_description="Surface staining observed after passivation.",
        root_cause="Rinse water conductivity drifted high between DI regenerations.",
        corrective_action="Tightened rinse conductivity monitoring and regeneration schedule.",
        keywords=("passivation", "stain", "rinse", "conductivity", "stainless"),
    ),
)

# --- Sample nonconformances (intake) — planted_root_cause is the answer key --

SAMPLE_NCS: dict[str, SampleNC] = {
    "NC-DEMO-001": SampleNC(
        nc_id="NC-DEMO-001",
        title="Anodize coating thickness below spec floor",
        part_number="PN-AL-3382",
        lot="LOT-AN-42",
        process="Type II sulfuric anodize",
        defect_description=(
            "Eddy-current readings on lot LOT-AN-42 show coating thickness of 0.4 mil, "
            "below the specified floor."
        ),
        spec_violated="SPEC-AN-7",
        measured_value="0.4 mil",
        required_value="0.7–1.2 mil",
        planted_root_cause=(
            "A mid-run rectifier output drop took bath voltage to ~11 V, pulling current "
            "density below the anodize window so coating growth stalled and finished thin."
        ),
    ),
    "NC-DEMO-002": SampleNC(
        nc_id="NC-DEMO-002",
        title="Electroless nickel adhesion failure on bend test",
        part_number="PN-ST-1190",
        lot="LOT-PL-17",
        process="Electroless nickel plating",
        defect_description=(
            "Plated deposit peeled from the basis metal during the bend-to-fracture "
            "adhesion test on lot LOT-PL-17."
        ),
        spec_violated="SPEC-PL-3",
        measured_value="Peeling observed",
        required_value="No lifting/peeling",
        planted_root_cause=(
            "The activation dwell ran only ~18 s against a 60–90 s window, leaving the "
            "surface under-activated so the deposit could not anchor."
        ),
    ),
    "NC-DEMO-003": SampleNC(
        nc_id="NC-DEMO-003",
        title="Etched slot width over upper tolerance",
        part_number="PN-CU-7741",
        lot="LOT-ET-09",
        process="Chemical etch",
        defect_description=(
            "Optical measurement of lot LOT-ET-09 shows slot width of 0.56 mm, above the "
            "upper tolerance limit."
        ),
        spec_violated="SPEC-ET-2",
        measured_value="0.56 mm",
        required_value="0.50 ± 0.02 mm",
        planted_root_cause=(
            "The etch bath ran ~32 °C against a 24–26 °C window; the elevated temperature "
            "raised the etch rate and over-cut the slot at fixed etch time."
        ),
    ),
    # Thin-evidence case: data is near-nominal, so no cause is supportable.
    "NC-DEMO-004": SampleNC(
        nc_id="NC-DEMO-004",
        title="Intermittent bore diameter excursion",
        part_number="PN-TI-5028",
        lot="LOT-MX-55",
        process="CNC milling",
        defect_description=(
            "One part in lot LOT-MX-55 measured 12.04 mm bore diameter, marginally over "
            "the upper limit; others were in tolerance."
        ),
        spec_violated="SPEC-DIM-1",
        measured_value="12.04 mm (1 of N)",
        required_value="12.00 ± 0.03 mm",
        planted_root_cause=(
            "Indeterminate from the available data — process parameters read nominal and a "
            "single marginal part is within measurement uncertainty; a gauge R&R and more "
            "sampling are needed before a cause can be claimed."
        ),
    ),
}
