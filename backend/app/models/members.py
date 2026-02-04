# app/models/member.py
from sqlalchemy import Column, Integer, String, Boolean, Timestamp, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Member(Base):
    # 1. 테이블 이름 정의
    __tablename__ = "member"

    # 2. 컬럼 정의 (테이블 정의서 내용 반영)
    member_no = Column(Integer, primary_key=True, autoincrement=True) # 회원 번호 (PK) 
    member_id = Column(String(50), nullable=False, unique=True)        # 회원 ID 
    passwd = Column(String, nullable=False)                            # 비밀번호 
    full_name = Column(String, nullable=False)                        # 성명 
    mobile_phone = Column(String(20), nullable=False)                  # 휴대전화번호 
    e_mail_address = Column(String, nullable=False)                   # 이메일 주소 
    
    # 농인 구분 (TRUE: 농인, FALSE: 일반인) 
    deaf_muteness_section_code = Column(Boolean, nullable=False, default=True)

    # 3. 등록/수정 정보 (테이블 정의서 공통 컬럼)
    create_user = Column(String(50), nullable=False) # 등록자 ID 
    create_date = Column(Timestamp, nullable=False, server_default=func.now()) # 등록 일시 
    update_user = Column(String(50), nullable=True)  # 수정자 ID 
    update_date = Column(Timestamp, nullable=True)   # 수정 일시 
    delete_user = Column(String(50), nullable=True)  # 삭제자 ID 
    delete_date = Column(Timestamp, nullable=True)   # 삭제 일시