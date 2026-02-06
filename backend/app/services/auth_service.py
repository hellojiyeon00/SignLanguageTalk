# backend/app/services/auth_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from app.api.schemas import UserSignup, UserLogin

class AuthService:
    """
    DB의 crypt() 함수를 활용하여 인증 로직을 처리하는 서비스 클래스입니다.
    """

    @staticmethod
    def create_user(db: Session, user_data: UserSignup):
        # 1. 아이디 중복 확인
        check_sql = text("""
            SELECT member_id FROM multicampus_schema.member 
            WHERE member_id = :id
        """)
        result = db.execute(check_sql, {"id": user_data.user_id}).fetchone()
        
        if result:
            raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

        # 2. 회원가입 INSERT (DB가 암호화 수행)
        # [수정] 파이썬 암호화 로직 제거 -> SQL의 crypt()가 처리
        insert_sql = text("""
            INSERT INTO multicampus_schema.member (
                member_id, passwd, full_name, mobile_phone, 
                e_mail_address, deaf_muteness_section_code, create_user
            ) VALUES (
                :id, 
                crypt(:pw, gen_salt('bf')),  -- 여기가 핵심! DB가 비밀번호를 암호화해서 저장함
                :name, :phone, :email, :is_deaf, :creator
            )
        """)

        params = {
            "id": user_data.user_id,
            "pw": user_data.password, # 평문을 그대로 보냄
            "name": user_data.user_name,
            "phone": user_data.phone_number,
            "email": user_data.email,
            "is_deaf": user_data.is_deaf,
            "creator": user_data.user_id
        }

        try:
            db.execute(insert_sql, params)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"가입 실패: {str(e)}")

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin):
        """
        로그인 시 DB에서 아이디와 비밀번호가 모두 맞는 사람을 찾습니다.
        """
        # [수정] 파이썬에서 verify_password를 안 쓰고, SQL 조건절에서 바로 검사
        login_sql = text("""
            SELECT member_id, full_name 
            FROM multicampus_schema.member
            WHERE member_id = :id 
              AND passwd = crypt(:pw, passwd) -- 비밀번호가 맞는지 DB가 확인
        """)
        
        user = db.execute(login_sql, {
            "id": login_data.user_id, 
            "pw": login_data.password
        }).fetchone()
        
        # user가 조회되면 성공, 아니면 실패(None)
        return user