# app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from jose import jwt
from app.api.schemas import UserSignup, UserLogin
from app.core.security import hash_password, verify_password
from app.core.config import settings

# 1. 라우터 설정 (서버의 주소 체계를 관리합니다)
router = APIRouter()

# 2. [임시 DB] 창주님 DB 구현 전까지 사용할 리스트 (테이블 정의서 규격 반영)
dummy_user_db = []

# 3. 친구 관계를 저장할 임시 장부 (누가 누구랑 친구인지)
dummy_friend_db = []

# --- [도우미 함수: JWT 입장권 발행] ---
def create_access_token(data: dict):
    """로그인 성공 시 '자유이용권(JWT)'을 만들어주는 함수입니다. """
    to_encode = data.copy()
    # 팔찌의 유효 기간을 설정합니다 (예: 30분)
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    # 우리 서버만 아는 비밀키로 도장을 찍어서 토큰을 만듭니다.
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- [F-MEM-01: 회원가입 기능] ---
@router.post("/signup")
def signup(user_data: UserSignup):
    # 1. 아이디 중복 확인 (테이블 정의서의 member_id 기준)
    for user in dummy_user_db:
        if user["member_id"] == user_data.user_id:
            raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

    # 2. 비밀번호 암호화 (bcrypt 알고리즘 적용)
    hashed_pw = hash_password(user_data.password)

    # 3. [중요] 테이블 정의서 [source 28-29] 규격에 맞춘 데이터 생성
    new_member = {
        "member_no": len(dummy_user_db) + 1,       # 회원 번호 (자동 증가 흉내)
        "member_id": user_data.user_id,             # 회원 ID (Column: member_id)
        "passwd": hashed_pw,                        # 암호화된 비밀번호 (Column: passwd)
        "full_name": user_data.user_name,           # 성명 (Column: full_name)
        "mobile_phone": user_data.phone_number,     # 휴대전화번호 (Column: mobile_phone)
        "e_mail_address": user_data.email,          # 이메일 주소 (Column: e_mail_address)
        "deaf_muteness_section_code": True,         # 농인 구분 (기본값: 농인) 
        "create_user": user_data.user_id,           # 등록자 ID (세션ID 대신 가입ID 사용) 
        "create_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 등록 일시 
    }
    
    # 4. 임시 저장소에 추가
    dummy_user_db.append(new_member)
    
    return {"message": f"{user_data.user_name}님, 수어톡 가입을 환영합니다!"}

# --- [F-MEM-04: 로그인 및 JWT 발급] ---
@router.post("/login")
def login(login_data: UserLogin):
    # 1. 저장된 회원 목록에서 아이디 찾기
    for user in dummy_user_db:
        if user["member_id"] == login_data.user_id:
            # 2. 비밀번호가 맞는지 확인
            if verify_password(login_data.password, user["passwd"]):
                # 3. [F-MEM-09] 인증 성공 시 JWT 발급 
                access_token = create_access_token(data={"sub": user["member_id"]})
                
                return {
                    "message": "로그인 성공!",
                    "access_token": access_token,  # 발급된 팔찌
                    "token_type": "bearer",        # 토큰의 종류
                    "user_name": user["full_name"]
                }
    
    # 4. 실패 시 에러 출력 (F-MEM-08)
    raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")

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