"""
Text Preprocessor

Backend -> Model Server 로 전달되기 전,
사용자 입력 텍스트를 정규화한다.
"""

from __future__ import annotations

import unicodedata

def normalize_input_text(text: str) -> str:
    """
    (무손실) 모델 서버로 전달하기 전 사용자 입력 텍스트 정규화.
    
    정책:
    - 유니코드 NFC 정규화
    - 개행 통일: \\r\\n, \\r -> \\n
    - 제어문자 제거: printable 문자만 유지 (탭/개행은 허용)
    - 앞뒤 공백 trim

    주의:
    - 하드 컷(text[:N]) 금지
    - 문장 분리(split(".")[0]) 금지
    - 로그용 축약 문자열을 모델 입력으로 사용 금지
    """
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    
    # 유니코드 NFC 정규화
    text = unicodedata.normalize("NFC", text)

    # 개행 통일
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 제어문자 제거 (탭/개행 허용)
    out = []
    for ch in text:
        if ch == "\n" or ch == "\t" or ch.isprintable():
            out.append(ch)
    text = "".join(out)

    # trim
    return text.strip()
