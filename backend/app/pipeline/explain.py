"""Plain-language explanations in the user's language, grounded in the FDA label text."""

import json
import re

import anthropic
from pydantic import BaseModel

from .. import config
from ..models import Explanation, Finding, Label, Medication, UiText

SYSTEM = """You explain a patient's existing medications in plain language for patients \
and family caregivers, many of them older adults with limited English or low literacy.

Rules:
- Use ONLY the FDA label excerpts and the prescription directions provided. If the \
excerpts don't say what a medicine is for, say that it isn't listed and to ask the pharmacist.
- Never recommend starting, stopping, skipping, or changing any medication or dose.
- how_to_take restates the prescription directions from the bottle, not the general label dosing.
- Write at about a 5th-grade reading level: short sentences, common words, no jargon.
- warnings: at most two of the most important points from the label, or an empty string.
- Write everything in the requested language. Keep drug names recognizable (add the \
local name in parentheses if helpful).
- Translate each safety finding's title and detail faithfully. Keep the advice to ask a \
pharmacist. Do not soften or strengthen it.
- ui: translate every string in ui_english into the requested language, keeping the \
meaning exact (these are schedule labels, schedule notes, and the disclaimer)."""


class TranslatedFinding(BaseModel):
    index: int
    title: str
    detail: str


class ExplainOutput(BaseModel):
    explanations: list[Explanation]
    findings: list[TranslatedFinding]
    ui: UiText


ENGLISH_UI = UiText(
    before_breakfast="Before breakfast",
    morning="Morning",
    before_lunch="Before lunch",
    midday="Midday",
    before_dinner="Before dinner",
    evening="Evening",
    bedtime="Bedtime",
    as_needed="Only when needed",
    with_food="Take with food",
    empty_stomach="Take on an empty stomach, before eating",
    timing_unclear="Timing unclear: confirm with your pharmacist",
    disclaimer=("PillPal explains your medicines. It does not give medical advice. Always "
                "check with your pharmacist or doctor before changing anything."),
)


def explain(meds: list[Medication], labels: dict[str, Label], findings: list[Finding],
            language: str) -> tuple[list[Explanation], list[Finding], UiText]:
    if config.DEMO_MODE:
        return template_explanations(meds, labels), findings, ENGLISH_UI

    context = {
        "language": config.LANGUAGES.get(language, "English"),
        "medications": [
            {
                "medication_id": med.id,
                "name_on_bottle": med.extracted.name,
                "standard_name": med.standard_name,
                "strength": med.extracted.strength,
                "prescription_directions": med.extracted.directions,
                "fda_label": _label_excerpt(labels.get(med.id)),
            }
            for med in meds
        ],
        "findings": [{"index": i, "title": f.title, "detail": f.detail} for i, f in enumerate(findings)],
        "ui_english": ENGLISH_UI.model_dump(),
    }

    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=config.MODEL,
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
        output_format=ExplainOutput,
        extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
        extra_body={"fallbacks": "default"},
    )
    output = response.parsed_output
    if response.stop_reason == "refusal" or output is None:
        return template_explanations(meds, labels), findings, ENGLISH_UI

    translated = {t.index: t for t in output.findings}
    localized = [
        f.model_copy(update={"title": translated[i].title, "detail": translated[i].detail})
        if i in translated else f
        for i, f in enumerate(findings)
    ]
    return output.explanations, localized, output.ui


def _label_excerpt(label: Label | None, limit: int = 3000) -> dict | None:
    """Label sections for the prompt. Interactions are covered by checks.py, not the AI."""
    if not label:
        return None
    return {
        "title": label.title,
        "indications": label.indications[:limit],
        "dosage": label.dosage[:limit],
        "warnings": label.warnings[:limit],
    }


def _first_sentences(text: str, limit: int = 300) -> str:
    text = " ".join(text.split())
    text = re.sub(r"^[\d.\s]*[A-Z][A-Z &]+\s", "", text)  # drop "1 INDICATIONS AND USAGE"
    if len(text) <= limit:
        return text
    cut = text.rfind(". ", 0, limit)
    return text[: cut + 1] if cut > 0 else text[:limit] + "…"


def template_explanations(meds: list[Medication], labels: dict[str, Label]) -> list[Explanation]:
    """English fallback that quotes the label directly (used in demo mode)."""
    out = []
    for med in meds:
        label = labels.get(med.id)
        out.append(Explanation(
            medication_id=med.id,
            display_name=med.extracted.name,
            purpose=(_first_sentences(label.indications) if label and label.indications
                     else "The official label wasn't found. Ask your pharmacist what this medicine is for."),
            how_to_take=med.extracted.directions or "Directions unclear. Ask your pharmacist.",
            warnings=_first_sentences(label.warnings, 200) if label and label.warnings else "",
        ))
    return out
