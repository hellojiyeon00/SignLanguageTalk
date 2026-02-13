"""
inference/loader.py

Loads tokenizer/model once and returns a bundle dict.
"""

from __future__ import annotations

import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pathlib import Path


def get_model_bundle() -> dict:
    checkpoint_path = os.environ.get("KOBART_CHECKPOINT")
    if not checkpoint_path:
        raise RuntimeError("KOBART_CHECKPOINT env is not set")
    
    ckpt_dir = Path(checkpoint_path).expanduser().resolve()
    if not ckpt_dir.exists():
        raise RuntimeError(f"Checkpoint path not found: {ckpt_dir}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint_path).to(device)
    model.eval()

    return {
        "tokenizer": tokenizer,
        "model": model,
        "device": device,
        "model_name": os.environ.get("MODEL_NAME", "kobart")
    }
