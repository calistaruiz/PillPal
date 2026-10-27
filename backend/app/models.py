"""Shared data schemas. This file is the contract between backend and frontend."""

from typing import Literal

from pydantic import BaseModel

TimeOfDay = Literal["morning", "midday", "evening", "bedtime"]
SlotName = Literal["before_breakfast", "morning", "before_lunch", "midday",
                   "before_dinner", "evening", "bedtime", "as_needed"]
# Schedule notes are codes, translated on screen through UiText.
NoteCode = Literal["with_food", "empty_stomach", "timing_unclear"]


# ---------- What the vision model reads off the photos ----------

class ExtractedMed(BaseModel):
    name: str                       # exactly as printed, e.g. "Lisinopril"
    strength: str | None            # e.g. "10 mg"
    directions: str | None          # label directions, verbatim
    times_per_day: int | None
    times_of_day: list[TimeOfDay]   # only when the label says so
    as_needed: bool
    with_food: bool | None          # True = with food, False = empty stomach
    prescriber: str | None
    source_images: list[int]       # which photos it appeared on (0-based)
    confidence: float               # 0.0 to 1.0
    unclear_fields: list[str]       # fields that were hard to read


class Extraction(BaseModel):
    medications: list[ExtractedMed]


# ---------- Grounding data ----------

class Citation(BaseModel):
    label: str
    url: str


class Label(BaseModel):
    """The parts of an FDA drug label (openFDA / DailyMed) that we use."""
    set_id: str
    title: str
    indications: str
    dosage: str
    warnings: str
    interactions: str
    url: str


class Medication(BaseModel):
    id: str
    extracted: ExtractedMed
    rxcui: str | None
    standard_name: str | None
    ingredients: list[str]
    label_found: bool
    citations: list[Citation]


# ---------- What the user sees ----------

class Finding(BaseModel):
    kind: Literal["interaction", "duplicate", "low_confidence", "not_found"]
    medication_ids: list[str]
    title: str
    detail: str
    evidence: str | None = None     # quoted source text (English, unedited)
    citation: Citation | None = None


class ScheduleItem(BaseModel):
    medication_id: str
    name: str
    dose: str | None
    notes: list[NoteCode]


class ScheduleSlot(BaseModel):
    slot: SlotName
    time: str | None
    items: list[ScheduleItem]


class Explanation(BaseModel):
    medication_id: str
    display_name: str
    purpose: str
    how_to_take: str
    warnings: str


class UiText(BaseModel):
    before_breakfast: str
    morning: str
    before_lunch: str
    midday: str
    before_dinner: str
    evening: str
    bedtime: str
    as_needed: str
    with_food: str
    empty_stomach: str
    timing_unclear: str
    disclaimer: str


class AnalysisResponse(BaseModel):
    language: str
    demo_mode: bool
    medications: list[Medication]
    explanations: list[Explanation]
    schedule: list[ScheduleSlot]
    findings: list[Finding]
    ui: UiText
