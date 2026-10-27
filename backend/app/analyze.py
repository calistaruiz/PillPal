"""Run the full pipeline: photos in, one combined and checked plan out."""

from concurrent.futures import ThreadPoolExecutor

from . import config
from .models import AnalysisResponse, Citation, ExtractedMed, Label, Medication
from .pipeline import checks, explain, extract, labels, normalize, schedule


def _ground(index: int, med: ExtractedMed) -> tuple[Medication, Label | None]:
    match = normalize.lookup(med.name, med.strength)
    ingredients = match.ingredients if match else []
    label = labels.fetch_label(match.rxcui if match else None, ingredients)

    citations = []
    if match:
        citations.append(Citation(label="RxNorm", url=normalize.rxnav_url(match.rxcui)))
    if label:
        citations.append(Citation(label=f"FDA label: {label.title}", url=label.url))

    return Medication(
        id=f"med-{index + 1}",
        extracted=med,
        rxcui=match.rxcui if match else None,
        standard_name=match.name if match else None,
        ingredients=ingredients,
        label_found=label is not None,
        citations=citations,
    ), label


def analyze(images: list[tuple[bytes, str]], language: str) -> AnalysisResponse:
    extracted = extract.demo_medications() if config.DEMO_MODE else extract.extract_medications(images)

    with ThreadPoolExecutor(max_workers=8) as pool:
        grounded = list(pool.map(lambda pair: _ground(*pair), enumerate(extracted)))
    meds = [med for med, _ in grounded]
    found_labels = {med.id: label for med, label in grounded if label}

    findings = (
        checks.find_interactions(meds, found_labels)
        + checks.find_duplicates(meds)
        + checks.find_reading_problems(meds)
    )
    explanations, findings, ui = explain.explain(meds, found_labels, findings, language)

    return AnalysisResponse(
        language=language,
        demo_mode=config.DEMO_MODE,
        medications=meds,
        explanations=explanations,
        schedule=schedule.build_schedule(meds),
        findings=findings,
        ui=ui,
    )
