# backend/app/models/members.py
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func
from app.core.database import Base

class Member(Base):
    # 1. 테이블 이름 및 스키마 설정
    __tablename__ = "member"
    __table_args__ = {'schema': 'multicampus_schema'} # 실제 DB 방 이름 명시

    # 2. 회원 정보 
    # member_no는 DB에서 GENERATED ALWAYS AS IDENTITY로 설정됨
    member_no = Column(Integer, primary_key=True, index=True) 
    member_id = Column(String(50), unique=True, index=True, nullable=False) # 길이 50 제한
    passwd = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    mobile_phone = Column(String(50), nullable=False) # 길이 50 제한
    e_mail_address = Column(String, nullable=False)
    
    # 3. 농인 여부 (기본값 TRUE)
    deaf_muteness_section_code = Column(Boolean, nullable=False, default=True)
    
    # 4. 관리 및 로그 정보 (TIMESTAMP WITHOUT TIME ZONE 반영)
    create_user = Column(String(50), nullable=False)
    # server_default를 사용하여 DB가 알아서 한국 시간을 찍도록 안내
    create_date = Column(TIMESTAMP(timezone=False), nullable=False, server_default=func.now())
    
    update_user = Column(String(50), nullable=True)
    update_date = Column(TIMESTAMP(timezone=False), nullable=True)
    delete_user = Column(String(50), nullable=True)
    delete_date = Column(TIMESTAMP(timezone=False), nullable=True)