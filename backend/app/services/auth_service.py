# backend/app/services/auth_service.py

# ==============================================================================
# 1. 라이브러리 임포트
# ==============================================================================
from sqlalchemy.orm import Session
from sqlalchemy import text # SQL문을 문자열로 작성하기 위해 필요합니다.
from fastapi import HTTPException

# 데이터 검증을 위해 설계도(Schema)를 가져옵니다.
from app.api.schemas import UserSignup, UserLogin, UserUpdate

class AuthService:
    """
    [인증 서비스 클래스]
    회원가입, 로그인 등 '사용자 계정'과 관련된 핵심 비즈니스 로직을 처리합니다.
    Raw SQL을 사용하여 PostgreSQL의 내장 암호화 함수(crypt)를 직접 활용합니다.
    """

    # @staticmethod: 클래스(AuthService)를 따로 생성(new)하지 않고도 바로 쓸 수 있게 해주는 장식입니다.
    # 사용법: AuthService.create_user(...)
    
    # ---------------------------------------------------------------------------
    # [1] 회원가입 처리
    # ---------------------------------------------------------------------------
    @staticmethod
    def create_user(db: Session, user_data: UserSignup):
        """
        [회원가입 로직]
        1. 아이디 중복 검사
        2. 비밀번호 암호화 및 DB 저장 (Transaction 관리)
        """
        
        # --------------------------------------------------------------------------
        # 1단계: 아이디 중복 확인
        # --------------------------------------------------------------------------
        
        # :id 처럼 콜론(:)이 붙은 부분은 나중에 변수로 채워넣을 자리(Placeholder)입니다.
        check_sql = text("""
            SELECT member_id FROM multicampus_schema.member 
            WHERE member_id = :id
        """)
        
        # 쿼리 실행 후 결과 한 줄(.fetchone)을 가져옵니다.
        result = db.execute(check_sql, {"id": user_data.user_id}).fetchone()
        
        # 만약 결과가 있다면(이미 존재하는 아이디라면), 400 에러를 내고 멈춥니다.
        if result:
            raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

        # --------------------------------------------------------------------------
        # 2단계: 회원 정보 저장 (INSERT)
        # --------------------------------------------------------------------------
        
        # [핵심] crypt(:pw, gen_salt('bf'))
        # - 파이썬에서 암호화를 하지 않고, 비밀번호 평문을 DB로 보냅니다.
        # - PostgreSQL이 받아서 'Blowfish(bf)' 알고리즘으로 암호화한 뒤 저장합니다.
        # - 이렇게 하면 DB 내부에서만 암호화가 이루어져 보안성이 유지됩니다.
        insert_sql = text("""
            INSERT INTO multicampus_schema.member (
                member_id, passwd, full_name, mobile_phone, 
                e_mail_address, deaf_muteness_section_code, create_user
            ) VALUES (
                :id, 
                crypt(:pw, gen_salt('bf')), 
                :name, :phone, :email, :is_deaf, :creator
            )
        """)

        # SQL문의 빈칸(:id, :pw ...)에 채워 넣을 실제 데이터들입니다.
        params = {
            "id": user_data.user_id,
            "pw": user_data.password,   # 여기는 평문이지만, 위 SQL에서 암호화됩니다.
            "name": user_data.user_name,
            "phone": user_data.phone_number,
            "email": user_data.email,
            "is_deaf": user_data.is_deaf,
            "creator": user_data.user_id # 생성자는 본인 아이디로 기록
        }

        # --------------------------------------------------------------------------
        # 3단계: 트랜잭션(Transaction) 처리
        # --------------------------------------------------------------------------
        try:
            db.execute(insert_sql, params) # SQL 실행 준비
            db.commit() # "진짜로 저장해!" (확정)
            
        except Exception as e:
            # 만약 저장하다가 에러가 나면(예: 인터넷 끊김, 데이터 오류 등)
            db.rollback() # "방금 하려던 거 취소해!" (되돌리기)
            
            # 사용자에게는 "서버 에러(500)"라고 알려줍니다.
            raise HTTPException(status_code=500, detail=f"가입 실패: {str(e)}")
        
    # ---------------------------------------------------------------------------
    # [2] 로그인 처리
    # ---------------------------------------------------------------------------
    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin):
        """
        [로그인 인증 로직]
        사용자가 입력한 아이디와 비밀번호가 DB에 저장된 정보와 일치하는지 확인합니다.
        """
        
        # --------------------------------------------------------------------------
        # DB 레벨에서의 비밀번호 검증
        # --------------------------------------------------------------------------
        # passwd = crypt(:pw, passwd)
        # 1. 사용자가 입력한 비밀번호(:pw)를 DB가 다시 암호화해봅니다.
        # 2. 그 결과가 DB에 저장되어 있던 passwd와 똑같은지 비교합니다.
        # 3. 아이디도 맞고(:id), 비밀번호도 맞아야 결과가 나옵니다.
        login_sql = text("""
            SELECT member_id, full_name 
            FROM multicampus_schema.member
            WHERE member_id = :id 
              AND passwd = crypt(:pw, passwd)
              AND delete_date IS NULL
        """)
        
        # 쿼리 실행
        user = db.execute(login_sql, {
            "id": login_data.user_id, 
            "pw": login_data.password
        }).fetchone()
        
        # user 변수에는 (member_id, full_name) 튜플이 들어있거나,
        # 일치하는 사람이 없으면 None이 들어있습니다.
        return user
    
    # ---------------------------------------------------------------------------
    # [3] 사용자 정보 조회
    # ---------------------------------------------------------------------------
    @staticmethod
    def get_user_info(db: Session, user_id: str):
        """
        설정 화면에 띄워줄 사용자 정보를 DB에서 가져옵니다.
        """
        sql = text("""
            SELECT member_id, full_name, mobile_phone, e_mail_address 
            FROM multicampus_schema.member 
            WHERE member_id = :id
        """)
        user = db.execute(sql, {"id": user_id}).fetchone()
        
        return user # 없으면 None 반환

    # ---------------------------------------------------------------------------
    # [4] 사용자 정보 수정
    # ---------------------------------------------------------------------------
    @staticmethod
    def update_user(db: Session, update_data: UserUpdate):
        """
        사용자가 입력한 정보로 DB를 업데이트합니다.
        비밀번호 변경 요청 여부에 따라 SQL이 달라집니다.
        """
        try:
            # 1) 비밀번호도 바꾸는 경우
            if update_data.password:
                update_sql = text("""
                    UPDATE multicampus_schema.member
                    SET full_name = :name,
                        mobile_phone = :phone,
                        passwd = crypt(:pw, gen_salt('bf')), -- 새 비밀번호 암호화
                        update_date = CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Seoul',
                        update_user = :id
                    WHERE member_id = :id
                """)
                params = {
                    "name": update_data.user_name, 
                    "phone": update_data.phone_number, 
                    "pw": update_data.password, 
                    "id": update_data.user_id
                }
            
            # 2) 정보만 바꾸는 경우 (비밀번호 제외)
            else:
                update_sql = text("""
                    UPDATE multicampus_schema.member
                    SET full_name = :name,
                        mobile_phone = :phone,
                        update_date = CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Seoul',
                        update_user = :id
                    WHERE member_id = :id
                """)
                params = {
                    "name": update_data.user_name, 
                    "phone": update_data.phone_number, 
                    "id": update_data.user_id
                }

            db.execute(update_sql, params)
            db.commit()
            
        except Exception as e:
            db.rollback()
            # 에러 메시지를 호출한 쪽(Router)으로 던져줍니다.
            raise e
        
    # ---------------------------------------------------------------------------
    # [5] 회원 탈퇴 처리
    # ---------------------------------------------------------------------------
    @staticmethod
    def delete_user(db: Session, user_id: str):
        """
        회원을 완전히 삭제하지 않고, 탈퇴 날짜(delete_date)를 기록하여 비활성화합니다.
        """
        delete_sql = text("""
            UPDATE multicampus_schema.member
            SET delete_date = CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Seoul',
                delete_user = :id
            WHERE member_id = :id
        """)
        
        try:
            db.execute(delete_sql, {"id": user_id})
            db.commit()
        except Exception as e:
            db.rollback()
            raise e