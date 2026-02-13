"""
Model Bridge API

Frontend -> Backend -> Model Server 연결용 엔드포인트
(DB / 로그인 의존 없음 - DEV 단계)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.model_client import ModelClient

router = APIRouter()
model_client = ModelClient()


class TranslateRequest(BaseModel):
    text: str


@router.post("/translate")
async def translate(req: TranslateRequest):
    """
    텍스트를 모델 서버로 전달하고 결과를 반환
    """
    try:
        result = await model_client.infer(req.text)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Model server error: {e}"
        )
    
    return {
        "input": req.text,
        "output": result
    }

