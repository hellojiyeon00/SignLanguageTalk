# backend/app/api/schemas.py

# ==============================================================================
# 1. 라이브러리 임포트
# ==============================================================================
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Pydantic 라이브러리 설명:
# - BaseModel: 모든 데이터 모델(설계도)의 부모 클래스입니다. 이를 상속받으면 데이터 검증 기능이 자동으로 생깁니다.
# - EmailStr: 문자열이 진짜 '이메일 형식(@)'인지 자동으로 검사해주는 도구입니다.
# - Field: 데이터에 대한 추가적인 설명(description)이나 제약조건(min_length 등)을 걸 때 사용합니다.

# ==============================================================================
# 2. 요청(Request) 스키마
# 프론트엔드 -> 백엔드로 데이터를 보낼 때, "이 양식을 꼭 지켜줘!"라고 검사하는 역할입니다.
# ==============================================================================

class UserSignup(BaseModel):
    """
    [회원가입 요청 양식]
    사용자가 가입할 때 입력해야 하는 필수 정보들을 정의합니다.
    """
    # ... : 필드가 '필수(Required)'라는 뜻입니다. (값이 없으면 에러 발생)
    user_id: str = Field(..., description="사용자 아이디") 
    # min_length=8: 비밀번호가 8글자 미만이면 서버가 자동으로 거절합니다.
    password: str = Field(..., min_length=8, description="비밀번호 (보안을 위해 8자 이상 필수)")
    user_name: str = Field(..., description="사용자 실명")
    phone_number: str = Field(..., description="휴대폰 번호 (예: 010-1234-5678)") 
    # EmailStr: "abc" 같은 엉뚱한 문자열이 들어오면 에러를 냅니다. "abc@gmail.com" 처럼 생겨야 통과됩니다.
    email: EmailStr = Field(..., description="이메일 주소")
    # 기본값(default)을 True로 설정했습니다. 값을 안 보내면 자동으로 True(농인)로 처리됩니다.
    is_deaf: bool = Field(True, description="농인 여부 (True: 농인, False: 청인)")

class UserLogin(BaseModel):
    """
    [로그인 요청 양식]
    로그인할 때는 아이디와 비밀번호, 딱 두 가지만 필요합니다.
    """
    user_id: str
    password: str

class UserUpdate(BaseModel):
    user_id: str
    # 수정할 수도 있고 안 할 수도 있으므로 Optional 처리
    user_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    

class RoomCreateRequest(BaseModel):
    """
    [채팅방 생성/입장 요청 양식]
    "나(my_id)랑 쟤(target_id)랑 대화하고 싶어요"라고 요청할 때 씁니다.
    """
    my_id: str      # 방을 요청하는 사람 (나)
    target_id: str  # 대화 상대방 (친구)

# ==============================================================================
# 3. 응답(Response) 스키마
# 백엔드 -> 프론트엔드로 데이터를 돌려줄 때, "이런 모양으로 줄게"라고 약속하는 영수증입니다.
# ==============================================================================

class MessageResponse(BaseModel):
    """
    [기본 메시지 응답]
    단순히 성공/실패 메시지만 보낼 때 사용합니다. (예: "가입을 환영합니다!")
    """
    message: str

class TokenResponse(BaseModel):
    """
    [로그인 성공 응답]
    로그인에 성공하면 '출입증(토큰)'과 '사용자 정보'를 함께 줍니다.
    """
    message: str        # 성공 메시지
    access_token: str   # JWT 액세스 토큰 (로그인 유지용 출입증)
    token_type: str     # 토큰의 타입 (보통 'bearer'라고 씁니다)
    user_id: str        # 사용자 아이디 (프론트엔드에서 저장해두고 씀)
    user_name: str      # 사용자 이름 (화면 상단에 'OOO님 환영합니다' 띄울 때 씀)

class RoomResponse(BaseModel):
    """
    [채팅방 정보 응답]
    채팅방 생성이나 입장에 성공했을 때, 그 방의 번호를 알려줍니다.
    """
    room_id: int    # 채팅방 고유 번호 (DB의 Primary Key)
    message: str    # 안내 메시지 (예: "새 채팅방 생성 완료")