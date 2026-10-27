"""Map a printed drug name to RxNorm: a standard ID (RxCUI) and active ingredients."""

from dataclasses import dataclass, field

from .http import get_json

RXNAV = "https://rxnav.nlm.nih.gov/REST"


@dataclass
class RxNormMatch:
    rxcui: str
    name: str
    ingredients: list[str] = field(default_factory=list)


def rxnav_url(rxcui: str) -> str:
    return f"https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={rxcui}"


def lookup(name: str, strength: str | None) -> RxNormMatch | None:
    term = f"{name} {strength or ''}".strip()
    data = get_json(f"{RXNAV}/approximateTerm.json", {"term": term, "maxEntries": 5})
    candidates = ((data or {}).get("approximateGroup") or {}).get("candidate") or []

    # The best-ranked candidate can be a retired RxCUI with no properties
    # (e.g. "Metformin 500 mg"). Use the first one that is still active.
    for candidate in candidates:
        rxcui = candidate["rxcui"]
        props = ((get_json(f"{RXNAV}/rxcui/{rxcui}/properties.json", {}) or {}).get("properties")) or {}
        if props:
            break
    else:
        return None
    match = RxNormMatch(rxcui=rxcui, name=props["name"])

    if props.get("tty") in ("IN", "MIN"):
        match.ingredients = [match.name.lower()]
        return match

    related = get_json(f"{RXNAV}/rxcui/{rxcui}/related.json", {"tty": "IN"}) or {}
    for group in (related.get("relatedGroup") or {}).get("conceptGroup") or []:
        for concept in group.get("conceptProperties") or []:
            ingredient = concept["name"].lower()
            if ingredient not in match.ingredients:
                match.ingredients.append(ingredient)
    return match
