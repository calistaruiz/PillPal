"""Read medications off photos of pill bottles and discharge paperwork."""

import base64

import anthropic

from .. import config
from ..models import ExtractedMed, Extraction

SYSTEM = """You read photos of prescription pill bottles, pharmacy labels, and hospital \
discharge paperwork for a medication assistant used by patients and caregivers.

Rules:
- Transcribe only what is printed. Never guess a drug name, strength, or direction. \
If something is unreadable, set it to null and list the field in unclear_fields.
- The same medication can appear on a bottle and on discharge paperwork. List it once \
and record every image index it appeared on in source_images. Different products are \
separate entries even when they share an ingredient.
- times_of_day: fill only when the text says when to take it (morning, noon, evening, \
bedtime). times_per_day: the number of doses per day if stated ("twice daily" = 2).
- as_needed is true for "as needed" / "PRN" directions.
- confidence is your confidence (0 to 1) that name, strength, and directions are all \
read correctly. Lower it for blur, glare, cut-off text, or handwriting.
- Text may be in any language. Keep directions in the original language.
- If an image contains no medication information, ignore it."""


class ExtractionError(Exception):
    pass


def extract_medications(images: list[tuple[bytes, str]]) -> list[ExtractedMed]:
    """images: (bytes, media_type) pairs. Calls Claude once with all photos."""
    content: list[dict] = []
    for index, (data, media_type) in enumerate(images):
        content.append({"type": "text", "text": f"Image {index}:"})
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.standard_b64encode(data).decode("utf-8"),
            },
        })
    content.append({"type": "text", "text": "List every medication shown in these images."})

    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=config.MODEL,
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": content}],
        output_format=Extraction,
        # Server-side refusal fallback: if a safety classifier declines, the API
        # retries on a fallback model inside the same call.
        extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
        extra_body={"fallbacks": "default"},
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise ExtractionError("We couldn't read these photos. Please try clearer photos.")
    return response.parsed_output.medications


def demo_medications() -> list[ExtractedMed]:
    """A realistic sample list for running without an API key.

    Includes a known interaction (warfarin + ibuprofen), a duplicate ingredient
    (Tylenol + Percocet both contain acetaminophen), and one blurry reading.
    """
    return [
        ExtractedMed(
            name="Warfarin", strength="5 mg", directions="Take 1 tablet by mouth once daily in the evening",
            times_per_day=1, times_of_day=["evening"], as_needed=False, with_food=None,
            prescriber="Dr. Patel", source_images=[0], confidence=0.95, unclear_fields=[],
        ),
        ExtractedMed(
            name="Ibuprofen", strength="400 mg", directions="Take 1 tablet every 6 hours as needed for pain",
            times_per_day=None, times_of_day=[], as_needed=True, with_food=True,
            prescriber="Dr. Nguyen", source_images=[1], confidence=0.92, unclear_fields=[],
        ),
        ExtractedMed(
            name="Tylenol Extra Strength", strength="500 mg", directions="Take 2 tablets every 6 hours as needed",
            times_per_day=None, times_of_day=[], as_needed=True, with_food=None,
            prescriber=None, source_images=[2], confidence=0.9, unclear_fields=[],
        ),
        ExtractedMed(
            name="Percocet", strength="5 mg/325 mg", directions="Take 1 tablet every 6 hours as needed for severe pain",
            times_per_day=None, times_of_day=[], as_needed=True, with_food=True,
            prescriber="Dr. Nguyen", source_images=[3], confidence=0.88, unclear_fields=[],
        ),
        ExtractedMed(
            name="Lisinopril", strength="10 mg", directions="Take 1 tablet by mouth every morning",
            times_per_day=1, times_of_day=["morning"], as_needed=False, with_food=None,
            prescriber="Dr. Patel", source_images=[4], confidence=0.55, unclear_fields=["strength"],
        ),
    ]
