from fastapi.testclient import TestClient

from app.main import app
from app.models import Label
from app.pipeline import labels, normalize

INGREDIENTS = {
    "warfarin": ["warfarin"],
    "ibuprofen": ["ibuprofen"],
    "tylenol extra strength": ["acetaminophen"],
    "percocet": ["acetaminophen", "oxycodone"],
    "lisinopril": ["lisinopril"],
}


def fake_lookup(name, strength):
    ingredients = INGREDIENTS.get(name.lower())
    return normalize.RxNormMatch(rxcui=f"rx-{name}", name=name, ingredients=ingredients) if ingredients else None


def fake_fetch_label(rxcui, ingredients):
    if ingredients == ["warfarin"]:
        return Label(set_id="w", title="Warfarin", indications="Used to prevent blood clots.",
                     dosage="", warnings="", interactions="NSAIDs increase bleeding risk.",
                     url="https://dailymed.example/w")
    return None


def client(monkeypatch):
    # No network in tests: stub RxNorm and openFDA.
    monkeypatch.setattr(normalize, "lookup", fake_lookup)
    monkeypatch.setattr(labels, "fetch_label", fake_fetch_label)
    return TestClient(app)


def test_health(monkeypatch):
    response = client(monkeypatch).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "demo_mode": True}


def test_analyze_demo_returns_full_plan(monkeypatch):
    response = client(monkeypatch).post("/api/analyze", data={"language": "es"})
    assert response.status_code == 200
    body = response.json()

    assert body["demo_mode"] is True
    assert len(body["medications"]) == 5
    assert len(body["explanations"]) == 5
    kinds = {f["kind"] for f in body["findings"]}
    assert {"interaction", "duplicate", "low_confidence"} <= kinds
    assert [s["slot"] for s in body["schedule"]] == ["morning", "evening", "as_needed"]


def test_rejects_non_image_upload(monkeypatch):
    response = client(monkeypatch).post(
        "/api/analyze",
        files={"files": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
