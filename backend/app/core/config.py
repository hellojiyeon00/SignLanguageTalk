# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv() # .env 파일의 내용을 읽어옵니다.

class Settings:
    # 이창주 님이 관리하실 PostgreSQL 주소
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password123@localhost:5432/signtalk")
    
    # JWT 발급을 위한 비밀키 [cite: 143]
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-123")
    ALGORITHM = "HS256"

settings = Settings()