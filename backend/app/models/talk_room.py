# backend/app/models/rooms.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.core.database import Base

class TalkRoom(Base):
    # 1. 테이블 이름 (방 이름까지 정확하게!)
    __tablename__ = "talk_room"
    __table_args__ = {'schema': 'multicampus_schema'} # 이창주 님의 스키마 적용

    # 2. 컬럼 정의 (설계도 내용 그대로)
    talk_room_id = Column(Integer, primary_key=True, nullable=False) # PK
    member_no1 = Column(Integer, nullable=False) # 참여자 1
    member_no2 = Column(Integer, nullable=False) # 참여자 2
    
    # 3. 관리 정보
    create_user = Column(String(50), nullable=False)
    create_date = Column(TIMESTAMP, nullable=False, server_default=func.now())
    
    update_user = Column(String(50), nullable=True)
    update_date = Column(TIMESTAMP, nullable=True)
    delete_user = Column(String(50), nullable=True)
    delete_date = Column(TIMESTAMP, nullable=True)