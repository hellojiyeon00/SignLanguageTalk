"""
Gloss Preprocessor

Model Server가 반환한 gloss 문자열을 URL 매핑 전에 정제한다.

- f:1 같은 시간/프레임 토큰은 보존
- # 같은 기호 제거
- 일반 토큰에 붙은 숫자 제거 (예: 지시1 -> 지시)
- 공백 정리
"""

import re

_DIGITS_AT_END = re.compile(r"\d+$")
_TIME_TOKEN = re.compile(r"^f:\d+$")


def clean_gloss(gloss: str) -> str:
    """
    모델 서버가 반환한 gloss 문자열을 URL 매핑 전에 정제합니다.

    처리 규칙:
    1) 공백 기준 토큰화
    2) '#' 제거
    3) 시간/프레임 토큰(f:1 등)은 보존 (단, 끝 구두점은 제거 후 판정)
    4) 일반 토큰은 끝에 붙은 숫자만 제거 (예: 지시1 -> 지시)
    5) 빈 토큰 제거 후 공백으로 재결합
    """
    if not isinstance(gloss, str):
        raise ValueError("gloss must be a string")
    
    gloss = gloss.strip()
    if not gloss:
        return ""

    # 우선 공백 단위로 토큰화
    tokens = gloss.split()
    out: list[str] = []

    for tok in tokens:
        tok = tok.replace("#", "").strip()
        if not tok:
            continue

        # f:1, f:. 같은 케이스 방어: f: 토큰은 끝 구두점만 제거 후 판정
        if tok.startswith("f:"):
            cand = tok.rstrip(".,;!?")
            if _TIME_TOKEN.match(cand):
                out.append(cand)
                continue

        # 일반 토큰: 끝 숫자 제거
        tok = _DIGITS_AT_END.sub("", tok).strip()
        if tok:
            out.append(tok)

    return " ".join(out)
