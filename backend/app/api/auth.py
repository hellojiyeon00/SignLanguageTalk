# backend/app/api/auth.py

# ==============================================================================
# 1. 라이브러리 및 모듈 임포트
# ==============================================================================
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt  # JWT 토큰 생성 및 복호화를 위한 라이브러리

# 우리가 만든 모듈들 가져오기
from app.core.database import get_db  # DB 세션을 생성하는 함수
from app.api.schemas import UserSignup, UserLogin, UserUpdate, MessageResponse, TokenResponse # 데이터 검증용 설계도(Schema)
from app.core.config import settings  # 환경 설정(비밀키, 알고리즘 등)
from app.services.auth_service import AuthService  # 실제 비즈니스 로직(요리사)을 담당하는 서비스 클래스

# APIRouter 객체 생성
# 이 라우터는 main.py에서 app.include_router()를 통해 메인 앱에 연결됩니다.
router = APIRouter()

# ==============================================================================
# 2. 토큰 생성 함수 (Helper Function)
# ==============================================================================
def create_access_token(data: dict):
    """
    사용자 인증 성공 시 발급할 JWT(Json Web Token)를 생성하는 함수입니다.
    이 토큰은 '출입증'과 같아서, 로그인 후 API를 사용할 때마다 제시해야 합니다.
    """
    # 1. 원본 데이터를 복사합니다. (원본 훼손 방지)
    to_encode = data.copy()
    
    # 2. 토큰 만료 시간 설정 (현재 시간 + 30분)
    # 만료 시간이 없으면 토큰이 영구적으로 유효해져서 보안에 취약해집니다.
    expire = datetime.utcnow() + timedelta(minutes=30)
    
    # 3. 데이터에 만료 시간('exp') 정보를 추가합니다.
    to_encode.update({"exp": expire})
    
    # 4. JWT 라이브러리를 사용해 암호화된 문자열(토큰)로 변환하여 반환합니다.
    # settings.SECRET_KEY: 우리 서버만 알고 있는 비밀키 (서명용)
    # settings.ALGORITHM: 암호화 알고리즘 (예: HS256)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# ==============================================================================
# 3. 회원가입 API (POST /signup)
# ==============================================================================
@router.post(
    "/signup", 
    status_code=status.HTTP_201_CREATED,  # 성공 시 201(Created) 상태 코드 반환
    response_model=MessageResponse        # 성공 시 응답 데이터 형식을 MessageResponse로 지정
)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """
    [회원가입 엔드포인트]
    프론트엔드로부터 회원 정보를 받아 가입 처리를 진행합니다.
    
    - user_data: UserSignup 스키마를 통해 입력값(아이디, 비번 등)을 자동으로 검증합니다.
    - db: Depends(get_db)를 통해 데이터베이스 연결 세션을 주입받습니다.
    """
    
    # [핵심] 실제 가입 로직(중복 체크, DB 저장, 암호화 등)은 'AuthService'에게 위임합니다.
    # 라우터는 "가입 시켜줘"라고 명령만 내리고, 구체적인 방법은 몰라도 됩니다.
    AuthService.create_user(db, user_data)
    
    # 작업이 에러 없이 끝나면 성공 메시지를 반환합니다.
    # response_model(MessageResponse)에 정의된 필드인 'message'에 값을 담아 보냅니다.
    return {"message": "가입을 환영합니다!"}

# ==============================================================================
# 4. 로그인 API (POST /login)
# ==============================================================================
@router.post(
    "/login", 
    response_model=TokenResponse # 성공 시 토큰과 유저 정보를 담은 TokenResponse 형식을 반환
)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    [로그인 엔드포인트]
    아이디와 비밀번호를 받아 확인하고, 맞다면 액세스 토큰을 발급합니다.
    """
    
    # 1. 서비스에게 인증 요청
    # "이 아이디(login_data)를 가진 회원이 있는지, 비밀번호가 맞는지 확인해줘"
    user = AuthService.authenticate_user(db, login_data)
    
    # 2. 인증 실패 처리
    # user가 None이면 아이디가 없거나 비밀번호가 틀린 경우입니다.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # 401: 인증되지 않음
            detail="아이디 또는 비밀번호가 틀렸습니다."
        )

    # 3. 인증 성공 시: 액세스 토큰(JWT) 발급
    # user 변수는 튜플 형태 (member_id, full_name)로 반환된다고 가정합니다.
    # user[0]은 member_id입니다. 토큰의 'sub'(subject) 필드에 아이디를 저장합니다.
    access_token = create_access_token(data={"sub": user[0]})
    
    # 4. 결과 반환
    # TokenResponse 스키마에 정의된 필드명과 정확히 일치하는 딕셔너리를 반환합니다.
    return {
        "message": "로그인 성공!",
        "access_token": access_token, # 위에서 만든 토큰
        "token_type": "bearer",       # 토큰 타입 (일반적으로 bearer 사용)
        "user_id": user[0],           # 사용자 아이디 (member_id)
        "user_name": user[1]          # 사용자 이름 (full_name) - 화면 표시용
    }
    
# ==============================================================================
# 5. 내 정보 조회 API (GET /me)
# ==============================================================================
@router.get("/me")
def get_my_info(user_id: str, db: Session = Depends(get_db)):
    """
    [설정] 내 프로필 정보를 불러옵니다.
    """
    # 서비스에게 "정보 가져와"라고 시킴
    user = AuthService.get_user_info(db, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="사용자 정보를 찾을 수 없습니다.")
        
    return {
        "user_id": user[0],
        "user_name": user[1],
        "phone_number": user[2],
        "email": user[3]
    }

# ==============================================================================
# 6. 회원 정보 수정 API (PUT /me)
# ==============================================================================
@router.put("/me", response_model=MessageResponse)
def update_member(data: UserUpdate, db: Session = Depends(get_db)):
    """
    [설정] 이름, 전화번호, 비밀번호를 수정합니다.
    """
    try:
        # 서비스에게 "수정해줘"라고 시킴 (비밀번호 처리 로직은 서비스가 알아서 함)
        AuthService.update_user(db, data)
        return {"message": "회원정보가 수정되었습니다."}
        
    except Exception as e:
        # 서비스에서 에러가 나서 넘어왔다면 여기서 처리
        raise HTTPException(status_code=500, detail=f"수정 실패: {str(e)}")

# ==============================================================================
# 7. 회원 탈퇴 API (DELETE /me)
# ==============================================================================
@router.delete("/me", response_model=MessageResponse)
def delete_member(user_id: str, db: Session = Depends(get_db)):
    """
    [설정] 회원을 탈퇴 처리합니다 (Soft Delete).
    """
    try:
        # 서비스에게 "삭제 처리해줘"라고 시킴
        AuthService.delete_user(db, user_id)
        return {"message": "탈퇴 처리가 완료되었습니다."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"탈퇴 실패: {str(e)}")