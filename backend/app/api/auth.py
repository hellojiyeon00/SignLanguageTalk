# backend/app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt

from app.core.database import get_db
from app.api.schemas import UserSignup, UserLogin
from app.core.config import settings
from app.services.auth_service import AuthService  # 서비스 호출

router = APIRouter()

# --- [토큰 생성 함수] ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# --- [회원가입] ---
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    # 모든 로직(암호화 포함)은 서비스와 DB가 처리합니다.
    AuthService.create_user(db, user_data)
    return {"message": "가입을 환영합니다!"}

# --- [로그인] ---
@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    # 서비스에게 "이 아이디랑 비번 맞는 사람 있어?" 라고 물어봅니다.
    user = AuthService.authenticate_user(db, login_data)
    
    # DB에서 조회가 안 되면(=아이디 없거나 비번 틀림) 실패
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="아이디 또는 비밀번호가 틀렸습니다."
        )

    # 성공 시 토큰 발급
    # user[0]: member_id, user[1]: full_name (SQL select 순서)
    access_token = create_access_token(data={"sub": user[0]})
    
    return {
        "message": "로그인 성공!",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user[0],
        "user_name": user[1] 
    }