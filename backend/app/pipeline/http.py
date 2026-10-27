"""GET JSON from public drug APIs, with a small on-disk cache.

The cache makes repeat lookups instant and lets a rehearsed demo keep working
if the venue wifi drops. Delete backend/.cache/ to clear it.
"""

import hashlib
import json

import httpx

from .. import config

_client = httpx.Client(timeout=10, headers={"User-Agent": "PillPal/0.1 (hackathon prototype)"})


def get_json(url: str, params: dict, secret_params: dict | None = None) -> dict | None:
    """Return parsed JSON, {} for "not found" (404), or None on network/server errors."""
    key = hashlib.sha256((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:24]
    path = config.CACHE_DIR / f"{key}.json"
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        pass

    try:
        response = _client.get(url, params={**params, **(secret_params or {})})
    except httpx.HTTPError:
        return None
    if response.status_code == 404:
        data: dict = {}
    elif response.status_code != 200:
        return None
    else:
        data = response.json()

    try:
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), "utf-8")
    except OSError:
        pass  # caching is best-effort (read-only disk, Windows path limits)
    return data
