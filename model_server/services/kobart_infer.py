"""
model_server.services.kobart_infer

KoBART inference wrapper.
- 프로세스 시작 시 모델 1회 로드
- infer(text)로 추론 진행
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from model_server.core.settings import settings


@dataclass
class InferResult:
    gloss: str
    meta: Dict


class KoBARTInfer:
    def __init__(self):
        # device 결정
        if settings.device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(settings.device)

        # tokenizer / model 로드
        self.tokenizer = AutoTokenizer.from_pretrained(
            settings.kobart_model_dir
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            settings.kobart_model_dir
        ).to(self.device)

        self.model.eval()

    @torch.inference_mode()
    def infer(self, text: str) -> InferResult:
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True
        ).to(self.device)

        model_inputs = dict(inputs)
        model_inputs.pop("token_type_ids", None)

        output_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=settings.max_new_tokens,
            num_beams=settings.num_beams
        )

        gloss = self.tokenizer.decode(
            output_ids[0],
            skip_special_token=True
        )

        return InferResult(
            gloss=gloss,
            meta={
                "device": str(self.device),
                "model_dir": settings.kobart_model_dir,
                "max_new_tokens": settings.max_new_tokens,
                "num_beams": settings.num_beams
            }
        )
