# backend/app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt

# 만든 모듈들 가져오기
from app.api.schemas import UserSignup, UserLogin
from app.core.security import hash_password, verify_password
from app.core.config import settings
from app.core.database import get_db
from app.models.members import Member 

router = APIRouter()

# 토큰 생성 함수
def create_access_token(data: dict):
    """로그인 성공 시 '자유이용권(JWT)'을 만들어주는 함수입니다. """
    to_encode = data.copy()
     # 팔찌의 유효 기간을 설정합니다 (예: 30분)
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    # 우리 서버만 아는 비밀키로 도장을 찍어서 토큰을 만듭니다.
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# [회원가입]
@router.post("/signup")
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    # 1. 아이디 중복 확인 (DB 조회)
    existing_user = db.query(Member).filter(Member.member_id == user_data.user_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

    # 2. 비밀번호 암호화
    hashed_pw = hash_password(user_data.password)

    # 3. 데이터 포장 (member_no는 DB가 자동생성 하므로 생략)
    new_member = Member(
        member_id=user_data.user_id,
        passwd=hashed_pw,
        full_name=user_data.user_name,
        mobile_phone=user_data.phone_number,
        e_mail_address=user_data.email,
        deaf_muteness_section_code=user_data.is_deaf, # 농인 여부
        create_user=user_data.user_id
    )
    
    # 4. 저장 (Commit)
    db.add(new_member)
    db.commit()
    
    return {"message": f"{user_data.user_name}님, 가입을 환영합니다!"}

# [로그인]
@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    # 1. 아이디 조회
    user = db.query(Member).filter(Member.member_id == login_data.user_id).first()
    
    # 2. 검증
    if not user or not verify_password(login_data.password, user.passwd):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")

    # 3. 토큰 발급
    access_token = create_access_token(data={"sub": user.member_id})
    
    return {
        "message": "로그인 성공!",
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user.full_name
    }

# [F-MEM-05] 전체 회원 목록 조회 (친구 목록용)
@router.get("/users")
def get_all_users():
    # 1. 보안을 위해 비밀번호는 빼고 줍니다.
    safe_users = []
    
    # 2. 저장된 모든 유저를 하나씩 꺼내서 포장합니다.
    for user in dummy_user_db:
        safe_info = {
            "user_id": user["member_id"],   # 아이디
            "user_name": user["full_name"]  # 이름
        }
        safe_users.append(safe_info)
    
    # 3. 안전한 명단만 반환합니다.
    return safe_users