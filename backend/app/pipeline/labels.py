"""Fetch the official FDA drug label (openFDA, same data as DailyMed)."""

from .. import config
from ..models import Label
from .http import get_json

OPENFDA = "https://api.fda.gov/drug/label.json"


def _section(result: dict, *names: str) -> str:
    # Keep full text: interaction tables often name specific drugs near the end.
    parts: list[str] = []
    for name in names:
        parts.extend(result.get(name) or [])
    return " ".join(parts)


def dailymed_url(set_id: str) -> str:
    return f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={set_id}"


def fetch_label(rxcui: str | None, ingredients: list[str]) -> Label | None:
    searches = [f'openfda.rxcui:"{rxcui}"'] if rxcui else []
    if ingredients:
        searches.append(" AND ".join(f'openfda.generic_name:"{i}"' for i in ingredients))

    secret = {"api_key": config.OPENFDA_API_KEY} if config.OPENFDA_API_KEY else None
    for search in searches:
        data = get_json(OPENFDA, {"search": search, "limit": 10}, secret)
        results = (data or {}).get("results") or []
        # A name search for "lisinopril" also returns lisinopril + HCTZ combination
        # labels. Only accept a label whose ingredient count matches.
        exact = [r for r in results
                 if len((r.get("openfda") or {}).get("substance_name") or []) == len(ingredients)]
        if exact:
            result = exact[0]
            openfda = result.get("openfda") or {}
            title = ((openfda.get("brand_name") or openfda.get("generic_name") or ["FDA label"])[0])
            set_id = result.get("set_id", "")
            return Label(
                set_id=set_id,
                title=title,
                indications=_section(result, "indications_and_usage", "purpose"),
                dosage=_section(result, "dosage_and_administration", "directions"),
                warnings=_section(result, "boxed_warning", "warnings_and_cautions", "warnings"),
                interactions=_section(result, "drug_interactions", "do_not_use", "ask_doctor_or_pharmacist"),
                url=dailymed_url(set_id),
            )
    return None
