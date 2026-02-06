# backend/app/models/members.py

# ==============================================================================
# 1. 라이브러리 임포트
# ==============================================================================
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func
from app.core.database import Base

class Member(Base):
    """
    [회원 테이블 모델]
    데이터베이스의 'multicampus_schema.member' 테이블과 연결된 클래스입니다.
    이 클래스의 객체 하나가 회원 한 명의 데이터를 의미합니다.
    """

    # ==========================================================================
    # 2. 테이블 기본 설정
    # ==========================================================================
    __tablename__ = "member"  # DB에 저장될 실제 테이블 이름
    
    # 스키마(폴더 같은 개념)를 지정합니다. 'multicampus_schema' 안에 있는 'member' 테이블을 씁니다.
    __table_args__ = {'schema': 'multicampus_schema'} 

    # ==========================================================================
    # 3. 컬럼 정의 (회원 핵심 정보)
    # ==========================================================================
    
    # 회원 번호 (Primary Key)
    # index=True: 검색 속도를 빠르게 하기 위해 색인을 만듭니다.
    # DB 설정에 따라 자동으로 숫자가 1씩 증가하며 생성됩니다.
    member_no = Column(Integer, primary_key=True, index=True) 
    
    # 회원 아이디
    # unique=True: 똑같은 아이디를 가진 사람이 없도록 강제합니다. (중복 방지)
    # nullable=False: 이 칸은 비워둘 수 없습니다. (필수 입력)
    member_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # 비밀번호
    # 암호화된 긴 문자열이 들어가므로 길이를 넉넉하게 잡거나 제한을 두지 않습니다(String).
    passwd = Column(String, nullable=False)
    
    # 사용자 성명 (실명)
    full_name = Column(String, nullable=False)
    
    # 휴대폰 번호
    mobile_phone = Column(String(50), nullable=False)
    
    # 이메일 주소
    e_mail_address = Column(String, nullable=False)
    
    # ==========================================================================
    # 4. 상태 정보
    # ==========================================================================
    
    # 농인 여부 구분 코드
    # True: 농인 / False: 청인 (기본값은 True로 설정)
    deaf_muteness_section_code = Column(Boolean, nullable=False, default=True)
    
    # ==========================================================================
    # 5. 관리 및 로그 정보 (Audit Log)
    # 누가 언제 만들고 수정했는지 기록하는 칸입니다. DB 관리를 위해 필수적입니다.
    # ==========================================================================
    
    # 생성자 ID (회원가입 시 본인 아이디가 들어감)
    create_user = Column(String(50), nullable=False)
    
    # 생성 일시
    # server_default=func.now(): 데이터를 넣을 때 파이썬이 시간을 안 알려주면, 
    # DB가 알아서 '현재 서버 시간'을 찍습니다.
    create_date = Column(TIMESTAMP(timezone=False), nullable=False, server_default=func.now())
    
    # 수정자 ID (정보 수정 시 기록)
    update_user = Column(String(50), nullable=True) # 처음엔 수정 안 했으니 비어있을 수 있음(True)
    
    # 수정 일시
    update_date = Column(TIMESTAMP(timezone=False), nullable=True)
    
    # 삭제자 ID (탈퇴 시 기록, 실제로 데이터를 지우지 않고 흔적을 남길 때 사용)
    delete_user = Column(String(50), nullable=True)
    
    # 삭제 일시
    delete_date = Column(TIMESTAMP(timezone=False), nullable=True)

    # ==========================================================================
    # 6. 디버깅용 출력 함수 (__repr__)
    # 개발자가 print(user)를 했을 때, 알아보기 쉬운 형태로 출력해주는 함수입니다.
    # 이게 없으면 <app.models.members.Member object at 0x7f...> 처럼 나옵니다.
    # ==========================================================================
    def __repr__(self):
        return f"<Member(no={self.member_no}, id='{self.member_id}', name='{self.full_name}')>"