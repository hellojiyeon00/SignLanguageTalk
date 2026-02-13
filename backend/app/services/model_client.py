"""
Model Client

Backend -> Model Server HTTP client
"""

from __future__ import annotations

import os
import time
import logging
import hashlib
from typing import Any, Dict, Optional
from app.services.gloss_preprocessor import clean_gloss

import httpx

logger = logging.getLogger(__name__)

MODEL_SERVER_BASE_URL = os.getenv("MODEL_SERVER_URL", "http://127.0.0.1:8001")
MODEL_SERVER_TIMEOUT_SEC = float(os.getenv("MODEL_SERVER_TIMEOUT_SEC", "10"))

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

class ModelClient:
    def __init__(self, base_url: str = MODEL_SERVER_BASE_URL, timeout_sec: float = MODEL_SERVER_TIMEOUT_SEC):
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    async def translate(self, text: str) -> Dict[str, Any]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        
        url = f"{self.base_url}/v1/translate"

        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            response = await client.post(url, json={"text": text})

        response.raise_for_status()

        data = response.json()
        gloss = data.get("gloss")
        meta: Optional[Dict[str, Any]] = data.get("meta") if isinstance(data.get("meta"), dict) else None

        if not isinstance(gloss, str) or not gloss.strip():
            raise RuntimeError("invalid model_server response: missing gloss")

        return {"gloss": gloss, "meta": meta}

    def translate_sync(self, text: str) -> Dict[str, Any]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        url = f"{self.base_url}/v1/translate"
        t0 = time.time()
        logger.info(f"[ModelClient] POST {url} timeout={self.timeout_sec}s text_len={len(text)}")
        logger.info(
            "[ModelClient] input_len=%d input_hash=%s preview=%r",
            len(text),
            _sha256(text),
            text[:80]
        )

        with httpx.Client(timeout=self.timeout_sec) as client:
            response = client.post(url, json={"text": text})

        elapsed_ms = int((time.time() - t0) * 1000)
        logger.info(f"[ModelClient] RESP {response.status_code} elapsed_ms={elapsed_ms}")

        response.raise_for_status()

        data = response.json()
        gloss = data.get("gloss")
        meta = data.get("meta") if isinstance(data.get("meta"), dict) else None

        if not isinstance(gloss, str) or not gloss.strip():
            raise RuntimeError("invalid model_server response: missing gloss")

        return {"gloss": gloss, "meta": meta}
    
