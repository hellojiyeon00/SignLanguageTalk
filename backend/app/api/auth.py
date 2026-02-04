# backend/app/api/auth.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text  # [필수] SQL 실행 도구
from datetime import datetime, timedelta
from jose import jwt

from app.api.schemas import UserSignup, UserLogin
from app.core.security import hash_password, verify_password
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()

# --- [토큰 생성 함수] ---
def create_access_token(data: dict):
    """로그인 성공 시 '자유이용권(JWT)'을 만들어주는 함수입니다. """
    to_encode = data.copy()
    # 팔찌의 유효 기간을 설정합니다 (예: 30분)
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    # 우리 서버만 아는 비밀키로 도장을 찍어서 토큰을 만듭니다.
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# --- [회원가입] ---
@router.post("/signup")
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    # 1. 아이디 중복 확인 (SQL)
    check_sql = text("""
        SELECT member_id FROM multicampus_schema.member 
        WHERE member_id = :id
    """)
    # 쿼리 실행 후 첫 번째 결과 가져오기
    result = db.execute(check_sql, {"id": user_data.user_id}).fetchone()
    
    if result:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

    # 2. 비밀번호 암호화
    hashed_pw = hash_password(user_data.password)

    # 3. INSERT SQL 작성
    insert_sql = text("""
        INSERT INTO multicampus_schema.member (
            member_id, passwd, full_name, mobile_phone, 
            e_mail_address, deaf_muteness_section_code, create_user
        ) VALUES (
            :id, :pw, :name, :phone, :email, :is_deaf, :creator
        )
    """)

    # 4. 데이터 매핑
    params = {
        "id": user_data.user_id,
        "pw": hashed_pw,
        "name": user_data.user_name,
        "phone": user_data.phone_number,
        "email": user_data.email,
        "is_deaf": user_data.is_deaf,
        "creator": user_data.user_id
    }

    # 5. 실행
    try:
        db.execute(insert_sql, params)
        db.commit() # 저장
    except Exception as e:
        db.rollback()
        print(f"에러 발생: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")
    
    return {"message": f"{user_data.user_name}님, 가입을 환영합니다!"}

# --- [로그인] ---
@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    # 1. 조회 SQL
    login_sql = text("""
        SELECT member_id, passwd, full_name 
        FROM multicampus_schema.member
        WHERE member_id = :id
    """)
    
    user = db.execute(login_sql, {"id": login_data.user_id}).fetchone()
    
    # 2. 검증 (user 순서: [0]no, [1]id, [2]passwd, [3]name)
    if not user or not verify_password(login_data.password, user[2]):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")

    # 3. 토큰 발급
    access_token = create_access_token(data={"sub": user[1]}) # user[1]은 member_id
    
    return {
        "message": "로그인 성공!",
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user[3] # user[3]는 full_name
    }