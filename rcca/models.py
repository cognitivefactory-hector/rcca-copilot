from django.db import models


class Nonconformance(models.Model):
    """A reported nonconformance — the input an RCCA investigates."""

    nc_id = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    part_number = models.CharField(max_length=100, blank=True)
    lot = models.CharField(max_length=100, blank=True)
    process = models.CharField(max_length=255, blank=True)
    defect_description = models.TextField(blank=True)
    spec_violated = models.CharField(max_length=255, blank=True)
    measured_value = models.CharField(max_length=255, blank=True)
    required_value = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nc_id} — {self.title}"


class Investigation(models.Model):
    """The 8D investigation for a nonconformance, made of gated sections."""

    nonconformance = models.ForeignKey(
        Nonconformance, on_delete=models.CASCADE, related_name="investigations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Investigation #{self.pk} for {self.nonconformance.nc_id}"

    @classmethod
    def create_for(cls, nonconformance):
        """Create an investigation and its five Drafted 8D sections."""
        from . import state

        investigation = cls.objects.create(nonconformance=nonconformance)
        for d_number in state.REQUIRED_D_NUMBERS:
            Section.objects.create(
                investigation=investigation,
                d_number=d_number,
                title=state.SECTION_TITLES[d_number],
            )
        return investigation

    @property
    def is_capa_ready(self):
        """Derived, never set: True iff all required sections are Approved."""
        from . import state

        return state.is_capa_ready(self)


class Section(models.Model):
    """One 8D section (by D-number) with its sign-off state."""

    class State(models.TextChoices):
        DRAFTED = "drafted", "Drafted"
        ENGINEER_EDITED = "engineer_edited", "Engineer-edited"
        APPROVED = "approved", "Approved"

    investigation = models.ForeignKey(
        Investigation, on_delete=models.CASCADE, related_name="sections"
    )
    d_number = models.CharField(max_length=4)
    title = models.CharField(max_length=255, blank=True)
    state = models.CharField(
        max_length=20, choices=State.choices, default=State.DRAFTED
    )
    agent_proposed_text = models.TextField(blank=True)
    current_text = models.TextField(blank=True)
    approver_name = models.CharField(max_length=255, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("investigation", "d_number")

    def __str__(self):
        return f"{self.d_number} ({self.get_state_display()})"


class CandidateCause(models.Model):
    """A proposed root cause under D4. Populated by the agent in M3."""

    class Category(models.TextChoices):
        MAN = "man", "Man"
        MACHINE = "machine", "Machine"
        METHOD = "method", "Method"
        MATERIAL = "material", "Material"
        MEASUREMENT = "measurement", "Measurement"
        ENVIRONMENT = "environment", "Environment"

    class Confidence(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="candidate_causes"
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()
    confidence = models.CharField(
        max_length=10, choices=Confidence.choices, blank=True
    )
    # The grounding rule (enforced in M3): a cause is either cited via an
    # EvidenceRef or explicitly flagged insufficient — never an uncited claim.
    insufficient_evidence = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_category_display()}: {self.description[:50]}"


class EvidenceRef(models.Model):
    """A citation tying a candidate cause to a retrieved evidence item."""

    candidate_cause = models.ForeignKey(
        CandidateCause, on_delete=models.CASCADE, related_name="evidence_refs"
    )
    source_type = models.CharField(max_length=50)  # process_data / spec / prior_nc
    source_id = models.CharField(max_length=100)
    locator = models.CharField(max_length=255, blank=True)
    excerpt = models.TextField(blank=True)

    def __str__(self):
        return f"{self.source_type}:{self.source_id}"


class AuditEvent(models.Model):
    """Append-only record of every state change — the audit trail.

    The diff between agent_proposed_text and the engineer's edits is the
    evidence of human judgment an auditor wants to see.
    """

    class EventType(models.TextChoices):
        DRAFT = "draft", "Draft"
        EDIT = "edit", "Edit"
        APPROVE = "approve", "Approve"
        REVERT = "revert", "Revert"

    investigation = models.ForeignKey(
        Investigation, on_delete=models.CASCADE, related_name="audit_events"
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=10, choices=EventType.choices)
    actor = models.CharField(max_length=255)
    from_state = models.CharField(max_length=20, blank=True)
    to_state = models.CharField(max_length=20, blank=True)
    text_snapshot = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "pk")

    def __str__(self):
        return f"{self.event_type} {self.section_id} by {self.actor}"
