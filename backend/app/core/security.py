# app/core/security.py
from passlib.context import CryptContext

# 비밀번호 암호화 도구 설정 (bcrypt 알고리즘 사용)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. 비밀번호를 암호로 바꾸는 함수
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 2. 입력한 비밀번호가 암호와 맞는지 확인하는 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)