# app/api/schemas.py
from pydantic import BaseModel, EmailStr, Field

# 회원가입 시 받을 정보 (회원가입 양식)
class UserSignup(BaseModel):
    user_id: str = Field(..., description="사용자 아이디") 
    password: str = Field(..., min_length=8, description="비밀번호 8자 이상")
    user_name: str = Field(..., description="사용자 성명")
    phone_number: str = Field(..., description="휴대폰 번호") 
    email: EmailStr = Field(..., description="이메일 주소")
    is_deaf: bool = Field(True, description="농인 여부 (True: 농인, False: 청인)")

# 로그인 시 받을 정보
class UserLogin(BaseModel):
    user_id: str
    password: str