"""
model_server/app.py

KoBART inference model server.
- Exposes POST /v1/translate
- Loads tokenizer/model once at startup
"""

from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from model_server.inference.generate import generate_gloss
from model_server.inference.loader import get_model_bundle


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    request_id: Optional[str] = None
    top_k: int = 1
    max_new_tokens: int = 64
    num_beams: int = 4


class TranslateResponse(BaseModel):
    request_id: str
    input: str
    gloss: str
    meta: dict


app = FastAPI(title="KoBART Model Server", version="1.0.0")

# tokenizer, model, divece, config
MODEL_BUNDLE = None


@app.on_event("startup")
def _startup() -> None:
    global MODEL_BUNDLE
    try:
        MODEL_BUNDLE = get_model_bundle()
        print("[startup] model loaded OK")
    except Exception as e:
        import traceback
        print("[startup] model load FAILED:", repr(e))
        traceback.print_exc()
        raise


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/v1/translate", response_model=TranslateResponse)
def transrate(req: TranslateRequest) -> TranslateResponse:
    if MODEL_BUNDLE is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    request_id = req.request_id or str(uuid.uuid4())
    t0 = time.time()

    # [DEBUG] 모델 서버 수신 텍스트 확인
    print(
        "[server<-client] has_dot=",
        ("." in req.text),
        "len=",
        len(req.text),
        "preview=",
        repr(req.text[:120])
    )

    try:
        gloss = generate_gloss(
            bundle=MODEL_BUNDLE,
            text=req.text,
            top_k=req.top_k,
            max_new_tokens=req.max_new_tokens,
            num_beams=req.num_beams
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"inference_failed: {e}")
    
    latency_ms = int((time.time() - t0) * 1000)    

    return TranslateResponse(
        request_id=request_id,
        input=req.text,
        gloss=gloss,
        meta={
            "model": MODEL_BUNDLE.get("model_name", "unknown"),
            "latency_ms": latency_ms,
            "device": MODEL_BUNDLE.get("device", "cpu")
        }
    )
