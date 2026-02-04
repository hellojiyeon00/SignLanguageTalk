# backend/app/models/members.py
from sqlalchemy import Column, Integer, String, Boolean, func, TIMESTAMP
from app.core.database import Base

class Member(Base):
    __tablename__ = "member"

    # 회원 정보 (필수 항목)
    member_no = Column(Integer, primary_key=True, index=True) # 자동 증가(IDENTITY)
    member_id = Column(String, unique=True, index=True, nullable=False)
    passwd = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    mobile_phone = Column(String, nullable=False)
    e_mail_address = Column(String, nullable=False)
    
    # 농인 여부 (True: 농인, False: 청인)
    deaf_muteness_section_code = Column(Boolean, nullable=False)
    
    # 관리 정보
    create_user = Column(String, nullable=False)
    create_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    update_user = Column(String(50), nullable=True)
    update_date = Column(TIMESTAMP(timezone=True), nullable=True)
    delete_user = Column(String(50), nullable=True)
    delete_date = Column(TIMESTAMP(timezone=True), nullable=True)