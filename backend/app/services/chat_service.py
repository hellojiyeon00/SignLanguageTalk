# backend/app/services/chat_service.py

# ==============================================================================
# 1. 라이브러리 임포트
# ==============================================================================
from sqlalchemy.orm import Session
from sqlalchemy import text # SQL문을 문자열로 작성하기 위해 필요
from fastapi import HTTPException

class ChatService:
    """
    [채팅 서비스 클래스]
    채팅방 생성, 친구 검색, 대화 목록 조회 등 채팅과 관련된 모든 DB 작업을 처리합니다.
    복잡한 조인(Join)이나 유니온(Union) 쿼리를 직접 작성하여 최적화된 데이터를 가져옵니다.
    """

    # ==========================================================================
    # 2. 사용자(친구) 검색
    # ==========================================================================
    @staticmethod
    def search_users(db: Session, my_id: str, name: str = None, member_id: str = None):
        """
        [친구 검색 로직]
        이름(name) 또는 아이디(member_id)로 사용자를 검색합니다.
        단, 검색하는 '나 자신'은 결과에서 제외합니다.
        """
        
        # 1. 검색 조건이 아예 없으면 빈 리스트를 반환합니다. (전체 회원 목록 노출 방지)
        if not name and not member_id:
            return []
        
        # 2. 기본 쿼리 작성 (나 자신을 제외하는 조건은 항상 포함)
        # :my_id 자리는 나중에 params로 채워집니다.
        query_str = """
            SELECT member_no, member_id, full_name 
            FROM multicampus_schema.member
            WHERE member_id != :my_id
        """
        params = {"my_id": my_id}
        
        # 3. 동적 쿼리 조립 (조건에 따라 SQL 문장을 덧붙입니다)
        
        # 이름으로 검색할 경우: LIKE 연산자 사용 (%검색어%)
        if name:
            query_str += " AND full_name LIKE :name"
            params["name"] = f"%{name}%"
        
        # 아이디로 검색할 경우
        if member_id:
            query_str += " AND member_id LIKE :member_id"
            params["member_id"] = f"%{member_id}%"
            
        # 4. 쿼리 실행 및 결과 변환
        results = db.execute(text(query_str), params).fetchall()
        
        # DB에서 꺼낸 튜플(row)을 프론트엔드가 쓰기 편한 딕셔너리로 바꿉니다.
        return [
            {"member_no": row[0], "member_id": row[1], "user_name": row[2]} 
            for row in results
        ]

    # ==========================================================================
    # 3. 채팅방 생성 또는 기존 방 입장
    # ==========================================================================
    @staticmethod
    def create_or_get_room(db: Session, my_id: str, target_id: str):
        """
        [채팅방 입장 로직]
        나와 상대방 사이의 1:1 채팅방을 찾습니다.
        - 이미 방이 있으면 -> 그 방의 번호(ID)를 반환
        - 방이 없으면 -> 새로 만들어서 번호를 반환
        """
        
        # 1. 두 사람의 회원 번호(member_no)를 먼저 알아냅니다. (아이디 -> 번호 변환)
        get_no_sql = text("SELECT member_no FROM multicampus_schema.member WHERE member_id = :id")
        my_no = db.execute(get_no_sql, {"id": my_id}).scalar()       # 내 번호
        target_no = db.execute(get_no_sql, {"id": target_id}).scalar() # 상대방 번호
        
        # 만약 한 명이라도 존재하지 않는 회원이라면 404 에러 발생
        if not my_no or not target_no:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # 2. 이미 존재하는 방인지 확인하는 쿼리
        # (내가 1번 참여자이고 상대가 2번 참여자인 경우) OR (반대의 경우) 모두 확인
        check_room_sql = text("""
            SELECT talk_room_id FROM multicampus_schema.talk_room
            WHERE (member_no1 = :m1 AND member_no2 = :m2)
               OR (member_no1 = :m2 AND member_no2 = :m1)
        """)
        room_id = db.execute(check_room_sql, {"m1": my_no, "m2": target_no}).scalar()

        # 방을 찾았다면 바로 그 방 번호를 반환합니다.
        if room_id:
            return {"room_id": room_id, "message": "이미 존재하는 채팅방입니다."}

        # 3. 방이 없으면 새로 생성 (INSERT)
        # nextval('...id_s')는 시퀀스를 사용해 자동으로 방 번호를 1 증가시킵니다.
        create_room_sql = text("""
            INSERT INTO multicampus_schema.talk_room (
                talk_room_id, member_no1, member_no2, create_user
            ) VALUES (
                nextval('multicampus_schema.talk_room_id_s'), :m1, :m2, :creator
            ) RETURNING talk_room_id
        """)
        
        try:
            # RETURNING talk_room_id 덕분에 방금 만든 방 번호를 바로 받아올 수 있습니다.
            new_room_id = db.execute(create_room_sql, {
                "m1": my_no, "m2": target_no, "creator": my_id
            }).scalar()
            
            db.commit() # 저장 확정
            return {"room_id": new_room_id, "message": "새 채팅방 생성 완료"}
            
        except Exception as e:
            db.rollback() # 에러 시 취소
            raise HTTPException(status_code=500, detail="채팅방 생성 실패")

    # ==========================================================================
    # 4. 내 채팅방 목록(친구 목록) 조회
    # ==========================================================================
    @staticmethod
    def get_my_rooms(db: Session, user_id: str):
        """
        [채팅방 목록 조회 로직]
        내가 참여하고 있는 모든 채팅방을 찾고, 각 방의 상대방 정보를 가져옵니다.
        쿼리가 다소 복잡한 이유는 내가 'member_no1'일 수도 있고 'member_no2'일 수도 있기 때문입니다.
        """
        
        # 1. 내 회원 번호 조회
        my_no_sql = text("SELECT member_no FROM multicampus_schema.member WHERE member_id = :id")
        my_no = db.execute(my_no_sql, {"id": user_id}).scalar()

        # 2. 채팅 목록 조회 쿼리 (UNION 사용)
        # 위쪽 SELECT: 내가 member_no1일 때 -> 상대방(member_no2) 정보를 가져옴
        # 아래쪽 SELECT: 내가 member_no2일 때 -> 상대방(member_no1) 정보를 가져옴
        # UNION: 두 결과를 합침
        chat_list_sql = text("""
            SELECT A1.member_no1 AS member_no,
                   (SELECT CC1.member_id FROM multicampus_schema.member CC1 WHERE A1.member_no1 = CC1.member_no) AS member_id,
                   (SELECT CC1.full_name FROM multicampus_schema.member CC1 WHERE A1.member_no1 = CC1.member_no) AS full_name
            FROM (
                SELECT BB1.member_no1, BB1.member_no2
                FROM multicampus_schema.member AA1, multicampus_schema.talk_room BB1
                WHERE AA1.member_no = :my_no 
                  AND (AA1.member_no = BB1.member_no1 OR AA1.member_no = BB1.member_no2)
            ) A1
            WHERE A1.member_no1 != :my_no
            UNION
            SELECT A2.member_no2 AS member_no,
                   (SELECT CC2.member_id FROM multicampus_schema.member CC2 WHERE A2.member_no2 = CC2.member_no) AS member_id,
                   (SELECT CC2.full_name FROM multicampus_schema.member CC2 WHERE A2.member_no2 = CC2.member_no) AS full_name
            FROM (
                SELECT BB2.member_no1, BB2.member_no2
                FROM multicampus_schema.member AA2, multicampus_schema.talk_room BB2
                WHERE AA2.member_no = :my_no 
                  AND (AA2.member_no = BB2.member_no1 OR AA2.member_no = BB2.member_no2)
            ) A2
            WHERE A2.member_no2 != :my_no
        """)
        
        results = db.execute(chat_list_sql, {"my_no": my_no}).fetchall()
        
        return [
            {"user_id": row[1], "user_name": row[2]} 
            for row in results
        ]

    # ==========================================================================
    # 5. 채팅 내역 조회
    # ==========================================================================
    @staticmethod
    def get_chat_history(db: Session, room_id: int):
        """
        [대화 내역 조회 로직]
        특정 채팅방(room_id)의 모든 메시지를 시간순(ASC)으로 가져옵니다.
        Talk 테이블과 Member 테이블을 조인(JOIN)하여 보낸 사람의 이름도 함께 가져옵니다.
        """
        history_sql = text("""
            SELECT T.message, M.member_id, M.full_name, T.talk_date
            FROM multicampus_schema.talk T
            JOIN multicampus_schema.member M ON T.member_no = M.member_no
            WHERE T.talk_room_id = :r_id
            ORDER BY T.talk_date ASC
        """)
        
        results = db.execute(history_sql, {"r_id": room_id}).fetchall()
        
        return [
            {
                "message": row[0], 
                "sender": row[1],      # 보낸 사람 아이디 (내가 보낸 건지 구분할 때 사용)
                "sender_name": row[2], # 보낸 사람 이름 (화면에 표시)
                "date": row[3].strftime("%H:%M") # 시간 포맷 (예: 14:30)
            } for row in results
        ]