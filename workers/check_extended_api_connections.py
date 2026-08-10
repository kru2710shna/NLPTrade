from __future__ import annotations

from pathlib import Path
import sys

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings


TIMEOUT = 20.0


def ok(name: str, detail: str = "") -> None:
    print(f" {name} OK {detail}")


def fail(name: str, error: Exception | str) -> None:
    print(f" {name} FAILED: {error}")


def test_thenewsapi() -> None:
    name = "TheNewsAPI"

    if not settings.thenewsapi_key:
        fail(name, "missing THENEWSAPI_KEY")
        return

    url = f"{settings.thenewsapi_base_url}/all"

    params = {
        "api_token": settings.thenewsapi_key,
        "search": "NVIDIA OR NVDA",
        "language": "en",
        "limit": 3,
    }

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        articles = data.get("data", [])
        count = len(articles)

        if count == 0:
            ok(name, "connected, but returned 0 articles for NVIDIA/NVDA")
            return

        sample = articles[0].get("title", "no title")
        ok(name, f"articles={count}, sample_title={sample}")

    except Exception as e:
        fail(name, e)


def test_huggingface_models() -> None:
    name = "Hugging Face Hub"

    if not settings.huggingface_api_key:
        fail(name, "missing HUGGINGFACE_API_KEY")
        return

    url = f"{settings.huggingface_base_url}/models"

    headers = {
        "Authorization": f"Bearer {settings.huggingface_api_key}",
    }

    params = {
        "search": "nvidia",
        "limit": 5,
        "sort": "lastModified",
        "direction": "-1",
    }

    try:
        with httpx.Client(timeout=TIMEOUT, headers=headers) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        if not data:
            ok(name, "connected, but returned 0 models for search=nvidia")
            return

        first = data[0]
        model_id = first.get("modelId") or first.get("id") or "unknown_model"
        downloads = first.get("downloads", "unknown")
        ok(name, f"models={len(data)}, sample_model={model_id}, downloads={downloads}")

    except Exception as e:
        fail(name, e)


def main() -> None:
    print("Checking extended API connections for NLPTrade...")
    print("-" * 80)

    test_thenewsapi()
    test_huggingface_models()

    print("-" * 80)
    print("Done.")


if __name__ == "__main__":
    main()
