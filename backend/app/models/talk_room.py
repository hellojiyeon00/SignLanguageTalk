# backend/app/models/talk_room.py

# ==============================================================================
# 1. 라이브러리 임포트
# ==============================================================================
from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.core.database import Base

class TalkRoom(Base):
    """
    [채팅방 테이블 모델]
    두 사용자 간의 1:1 대화방 정보를 저장하는 테이블입니다.
    데이터베이스의 'multicampus_schema.talk_room' 테이블과 연결됩니다.
    """

    # ==========================================================================
    # 2. 테이블 기본 설정
    # ==========================================================================
    __tablename__ = "talk_room"
    __table_args__ = {'schema': 'multicampus_schema'} # DB 스키마 지정

    # ==========================================================================
    # 3. 핵심 컬럼 정의
    # ==========================================================================
    
    # 채팅방 고유 번호 (PK)
    # 채팅방이 새로 생길 때마다 번호가 부여됩니다.
    talk_room_id = Column(Integer, primary_key=True, index=True, nullable=False)

    # 참여자 1의 회원 번호 (Member 테이블의 member_no)
    member_no1 = Column(Integer, nullable=False)
    
    # 참여자 2의 회원 번호
    # (참고: 채팅방은 두 사람의 member_no 조합으로 유일하게 식별됩니다)
    member_no2 = Column(Integer, nullable=False)
    
    # ==========================================================================
    # 4. 관리 및 로그 정보 (Audit Log)
    # Member 모델과 동일하게 생성/수정/삭제 이력을 남깁니다.
    # ==========================================================================
    
    # 방 만든 사람 (생성자 ID)
    create_user = Column(String(50), nullable=False)
    
    # 생성 일시 (서버 시간 자동 입력)
    # timezone=False 옵션을 주어 Member 테이블과 형식을 맞춥니다.
    create_date = Column(TIMESTAMP(timezone=False), nullable=False, server_default=func.now())
    
    # 수정 정보 (방 상태 변경 시 사용)
    update_user = Column(String(50), nullable=True)
    update_date = Column(TIMESTAMP(timezone=False), nullable=True)
    
    # 삭제 정보 (방 폭파 시 사용 - 실제 삭제 대신 기록만 남길 경우)
    delete_user = Column(String(50), nullable=True)
    delete_date = Column(TIMESTAMP(timezone=False), nullable=True)

    # ==========================================================================
    # 5. 디버깅용 출력 함수 (__repr__)
    # ==========================================================================
    def __repr__(self):
        return f"<TalkRoom(id={self.talk_room_id}, members={self.member_no1}&{self.member_no2})>"