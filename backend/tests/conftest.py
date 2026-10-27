import os

# Tests never call Claude. Set before app.config is imported.
os.environ["PILLPAL_DEMO_MODE"] = "true"

import pytest  # noqa: E402

from app.models import ExtractedMed, Label, Medication  # noqa: E402


def make_med(id: str, name: str, ingredients: list[str], **extracted) -> Medication:
    fields = dict(
        name=name, strength="10 mg", directions=None, times_per_day=None, times_of_day=[],
        as_needed=False, with_food=None, prescriber=None, source_images=[0],
        confidence=0.95, unclear_fields=[],
    )
    fields.update(extracted)
    return Medication(
        id=id, extracted=ExtractedMed(**fields), rxcui=f"rx-{id}", standard_name=name,
        ingredients=ingredients, label_found=True, citations=[],
    )


def make_label(interactions: str) -> Label:
    return Label(set_id="abc", title="Test label", indications="", dosage="", warnings="",
                 interactions=interactions, url="https://dailymed.example/abc")


@pytest.fixture
def med():
    return make_med


@pytest.fixture
def label():
    return make_label
