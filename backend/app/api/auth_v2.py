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
        "deaf_muteness_section_code": user_data.is_deaf,         # 농인 구분 (기본값: 농인) 
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
            # 2. 비밀번호가 맞는지 확인 [cite: 114]
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

# --- [기존 get_all_users 수정] ---
# 이제 '전체 회원'이 아니라 '내 친구'만 보여줘야 합니다!
@router.get("/friends")
def get_my_friends(user_id: str): # 요청한 사람(나)의 ID를 받습니다.
    my_friends = []
    
    # 1. 친구 장부를 뒤져서 '나'와 관련된 기록을 찾습니다.
    for record in dummy_friend_db:
        if record["user_id"] == user_id:
            # 2. 친구의 ID를 알아냅니다.
            friend_id = record["friend_id"]
            
            # 3. 그 친구의 상세 정보(이름 등)를 회원 명단에서 찾습니다.
            for user in dummy_user_db:
                if user["member_id"] == friend_id:
                    my_friends.append({
                        "user_id": user["member_id"],
                        "user_name": user["full_name"]
                    })
                    break
    return my_friends

# --- [F-CHAT-01] 친구 검색 기능 (새로 추가) ---
@router.get("/search")
def search_users(keyword: str, user_id: str):
    found_users = []
    
    # 1. 전체 회원을 뒤져서 검색어(keyword)가 포함된 사람을 찾습니다.
    for user in dummy_user_db:
        # (나 자신은 검색되면 안 됨)
        if user["member_id"] == user_id:
            continue
            
        # 2. 아이디나 이름에 검색어가 들어있는지 확인
        if keyword in user["member_id"] or keyword in user["full_name"]:
            # 3. 이미 친구인지 확인 (친구면 검색 결과에서 뺄 수도 있음)
            is_friend = False
            for record in dummy_friend_db:
                if record["user_id"] == user_id and record["friend_id"] == user["member_id"]:
                    is_friend = True
                    break
            
            # 친구가 아닐 때만 결과에 추가 (추가 버튼을 띄우기 위해)
            if not is_friend:
                found_users.append({
                    "user_id": user["member_id"],
                    "user_name": user["full_name"]
                })
                
    return found_users

# --- [F-CHAT-02, 03] 친구 추가 기능 (새로 추가) ---
from pydantic import BaseModel

class FriendRequest(BaseModel):
    user_id: str   # 나
    friend_id: str # 추가할 친구

@router.post("/friends")
def add_friend(request: FriendRequest):
    # 1. 이미 추가된 친구인지 다시 한 번 확인 (중복 방지)
    for record in dummy_friend_db:
        if record["user_id"] == request.user_id and record["friend_id"] == request.friend_id:
            return {"message": "이미 등록된 친구입니다."}

    # 2. 장부에 기록 (단방향 추가: 나는 너를 친구로, 너는 나를 아직 모름)
    # 카카오톡처럼 상대방 수락 없이 바로 추가되게 구현했습니다. (MVP 버전)
    dummy_friend_db.append({
        "user_id": request.user_id,
        "friend_id": request.friend_id,
        "status": "accepted"
    })
    
    # (선택) 양방향으로 하려면 반대쪽 기록도 추가해주면 됩니다.
    
    return {"message": "친구 목록에 추가되었습니다!"}