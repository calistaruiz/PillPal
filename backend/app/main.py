"""PillPal API. Run with: uvicorn app.main:app --reload"""

import anthropic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .analyze import analyze
from .models import AnalysisResponse
from .pipeline.extract import ExtractionError

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGES = 10
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # Claude's per-image limit

app = FastAPI(title="PillPal API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "demo_mode": config.DEMO_MODE}


@app.get("/api/languages")
def languages():
    return config.LANGUAGES


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_photos(
    files: list[UploadFile] = File(default=[]),
    language: str = Form("en"),
):
    if language not in config.LANGUAGES:
        language = "en"
    if not files and not config.DEMO_MODE:
        raise HTTPException(400, "Add at least one photo.")
    if len(files) > MAX_IMAGES:
        raise HTTPException(400, f"Please add {MAX_IMAGES} photos or fewer.")

    images = []
    for f in files:
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(400, f"{f.filename}: please use a JPEG, PNG, or WebP photo.")
        data = f.file.read()
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(400, f"{f.filename} is too large (max 5 MB).")
        images.append((data, f.content_type))

    try:
        return analyze(images, language)
    except ExtractionError as e:
        raise HTTPException(422, str(e))
    except anthropic.APIError as e:
        raise HTTPException(502, f"The AI service had a problem: {e.__class__.__name__}. Please try again.")
