from app.pipeline import normalize

RESPONSES = {
    "approximateTerm.json": {"approximateGroup": {"candidate": [{"rxcui": "316256"}, {"rxcui": "861007"}]}},
    "rxcui/316256/properties.json": {},  # retired concept: no properties
    "rxcui/861007/properties.json": {"properties": {"name": "metformin hydrochloride 500 MG Oral Tablet", "tty": "SCD"}},
    "rxcui/861007/related.json": {"relatedGroup": {"conceptGroup": [{"conceptProperties": [{"name": "Metformin"}]}]}},
}


def fake_get_json(url, params, secret_params=None):
    return next((v for k, v in RESPONSES.items() if url.endswith(k)), None)


def test_skips_retired_candidates(monkeypatch):
    monkeypatch.setattr(normalize, "get_json", fake_get_json)

    match = normalize.lookup("Metformin", "500 mg")

    assert match.rxcui == "861007"
    assert match.ingredients == ["metformin"]


def test_no_active_candidate_returns_none(monkeypatch):
    monkeypatch.setattr(normalize, "get_json", lambda url, params, secret_params=None: {
        "approximateGroup": {"candidate": [{"rxcui": "1"}]}} if "approximateTerm" in url else {})

    assert normalize.lookup("Nonsense", None) is None
