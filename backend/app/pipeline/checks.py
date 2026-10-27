"""Deterministic safety checks. No AI here: every finding points at its source."""

import re
from itertools import combinations

from .. import config
from ..models import Citation, Finding, Label, Medication
from .normalize import rxnav_url

# FDA labels often name a drug class ("NSAIDs") rather than each drug.
# Map class phrases to the ingredients they cover.
_NSAIDS = {"ibuprofen", "naproxen", "aspirin", "diclofenac", "celecoxib", "meloxicam",
           "ketorolac", "indomethacin", "etodolac", "nabumetone"}
_ANTICOAGULANTS = {"warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban",
                   "heparin", "enoxaparin"}
_SSRIS = {"sertraline", "fluoxetine", "citalopram", "escitalopram", "paroxetine", "fluvoxamine"}
_ACE_INHIBITORS = {"lisinopril", "enalapril", "ramipril", "benazepril", "captopril",
                   "quinapril", "fosinopril"}
_OPIOIDS = {"oxycodone", "hydrocodone", "morphine", "tramadol", "codeine",
            "hydromorphone", "fentanyl", "methadone"}
_BENZOS = {"alprazolam", "lorazepam", "diazepam", "clonazepam", "temazepam"}

CLASS_TERMS: dict[str, set[str]] = {
    "nsaid": _NSAIDS,
    "nsaids": _NSAIDS,
    "nonsteroidal anti-inflammatory": _NSAIDS,
    "anticoagulant": _ANTICOAGULANTS,
    "anticoagulants": _ANTICOAGULANTS,
    "blood thinner": _ANTICOAGULANTS,
    "ssri": _SSRIS,
    "ssris": _SSRIS,
    "selective serotonin reuptake inhibitor": _SSRIS,
    "ace inhibitor": _ACE_INHIBITORS,
    "ace inhibitors": _ACE_INHIBITORS,
    "opioid": _OPIOIDS,
    "opioids": _OPIOIDS,
    "benzodiazepine": _BENZOS,
    "benzodiazepines": _BENZOS,
}

ASK_PHARMACIST = "Please ask your pharmacist or doctor before changing anything."


def _terms_for(med: Medication) -> list[str]:
    terms = list(med.ingredients)
    terms += [phrase for phrase, members in CLASS_TERMS.items() if members & set(med.ingredients)]
    return terms


def _evidence(text: str, term: str) -> str | None:
    match = re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE)
    if not match:
        return None
    sentence_start = text.rfind(". ", 0, match.start())
    sentence_start = 0 if sentence_start == -1 else sentence_start + 2
    sentence_end = text.find(". ", match.end())
    sentence_end = len(text) if sentence_end == -1 else sentence_end + 1

    # Long sentences (often flattened tables): quote ~200 chars either side, on word boundaries.
    start, prefix = sentence_start, ""
    if match.start() - sentence_start > 200:
        start, prefix = text.find(" ", match.start() - 200) + 1, "…"
    end, suffix = sentence_end, ""
    if sentence_end - match.end() > 200:
        end, suffix = text.rfind(" ", 0, match.end() + 200), "…"
    return prefix + text[start:end].strip() + suffix


def _name(med: Medication) -> str:
    return med.extracted.name


def find_duplicates(meds: list[Medication]) -> list[Finding]:
    findings = []
    for a, b in combinations(meds, 2):
        shared = sorted(set(a.ingredients) & set(b.ingredients))
        if not shared:
            continue
        findings.append(Finding(
            kind="duplicate",
            medication_ids=[a.id, b.id],
            title=f"Same ingredient in two medicines: {', '.join(shared)}",
            detail=(f"{_name(a)} and {_name(b)} both contain {', '.join(shared)}. "
                    f"Taking both could mean taking too much. {ASK_PHARMACIST}"),
            citation=Citation(label="RxNorm (U.S. National Library of Medicine)",
                              url=rxnav_url(a.rxcui or b.rxcui or "")),
        ))
    return findings


def find_interactions(meds: list[Medication], labels: dict[str, Label]) -> list[Finding]:
    findings = []
    for a, b in combinations(meds, 2):
        if set(a.ingredients) & set(b.ingredients):
            continue  # reported as a duplicate instead
        hit = _search_label(a, b, labels) or _search_label(b, a, labels)
        if not hit:
            continue
        source, other, evidence, label = hit
        findings.append(Finding(
            kind="interaction",
            medication_ids=[a.id, b.id],
            title=f"Possible interaction: {_name(a)} + {_name(b)}",
            detail=(f"The official FDA label for {_name(source)} mentions {_name(other)} "
                    f"or its drug type. {ASK_PHARMACIST}"),
            evidence=evidence,
            citation=Citation(label=f"FDA label: {label.title} (DailyMed)", url=label.url),
        ))
    return findings


def _search_label(source: Medication, other: Medication, labels: dict[str, Label]):
    label = labels.get(source.id)
    if not label or not label.interactions:
        return None
    for term in _terms_for(other):
        evidence = _evidence(label.interactions, term)
        if evidence:
            return source, other, evidence, label
    return None


def find_reading_problems(meds: list[Medication]) -> list[Finding]:
    findings = []
    for med in meds:
        e = med.extracted
        if e.confidence < config.LOW_CONFIDENCE or e.unclear_fields:
            unclear = f" Hard to read: {', '.join(e.unclear_fields)}." if e.unclear_fields else ""
            findings.append(Finding(
                kind="low_confidence",
                medication_ids=[med.id],
                title=f"Please double-check: {e.name}",
                detail=(f"Part of this label was hard to read.{unclear} "
                        "Compare it with the bottle, or ask your pharmacist to confirm."),
            ))
        if not med.rxcui:
            findings.append(Finding(
                kind="not_found",
                medication_ids=[med.id],
                title=f"Couldn't match: {e.name}",
                detail=("We couldn't find this name in the U.S. drug database, so it was not "
                        "included in the safety checks. Ask your pharmacist about it."),
            ))
    return findings
