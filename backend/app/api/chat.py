# backend/app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from pydantic import BaseModel
from app.core.database import get_db

router = APIRouter()

# --- [요청 양식] ---
class RoomCreateRequest(BaseModel):
    my_id: str
    target_id: str

# 1. 🔍 사용자 검색 API
# "친구 추가" 대신, 아이디나 이름으로 검색해서 찾습니다.
@router.get("/search")
def search_user(
    my_id: str, 
    name: Optional[str] = None,      # 이름 (선택)
    member_id: Optional[str] = None, # 아이디 (선택)
    db: Session = Depends(get_db)
):
    # 1. 아무것도 입력 안 했으면 빈 리스트 반환
    if not name and not member_id:
        return []
    
    # 2. 기본 쿼리 (나 자신은 제외)
    query_str = """
        SELECT member_no, member_id, full_name 
        FROM multicampus_schema.member
        WHERE member_id != :my_id
    """
    params = {"my_id": my_id}
    
    # 3. 조건에 따라 SQL 덧붙이기 (조립)
    if name:
        query_str += " AND full_name LIKE :name"
        params["name"] = f"%{name}%"
    
    if member_id:
        query_str += " AND member_id LIKE :member_id"
        params["member_id"] = f"%{member_id}%"
        
    # %keyword% 형태로 만들어서 부분 검색이 되게 합니다.
    results = db.execute(text(query_str), params).fetchall()
    
    # 결과를 예쁜 리스트로 포장합니다.
    return [
        {"member_no": row[0], "member_id": row[1], "user_name": row[2]} 
        for row in results
    ]

# 2. 🚪 채팅방 만들기 (혹은 입장하기) API
# 검색된 사람을 클릭하면 실행됩니다.
@router.post("/room")
def get_or_create_room(req: RoomCreateRequest, db: Session = Depends(get_db)):
    # (1) 내 번호(no)와 상대방 번호(no)를 먼저 알아냅니다.
    get_no_sql = text("SELECT member_no FROM multicampus_schema.member WHERE member_id = :id")
    my_no = db.execute(get_no_sql, {"id": req.my_id}).scalar()
    target_no = db.execute(get_no_sql, {"id": req.target_id}).scalar()
    
    if not my_no or not target_no:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # (2) 이미 둘 사이에 만들어진 방이 있는지 확인합니다.
    # (내가 1번이고 걔가 2번이거나) OR (내가 2번이고 걔가 1번인 경우)
    check_room_sql = text("""
        SELECT talk_room_id FROM multicampus_schema.talk_room
        WHERE (member_no1 = :m1 AND member_no2 = :m2)
           OR (member_no1 = :m2 AND member_no2 = :m1)
    """)
    room_id = db.execute(check_room_sql, {"m1": my_no, "m2": target_no}).scalar()

    # (3) 방이 있으면 -> 그 방 번호를 바로 줍니다.
    if room_id:
        return {"room_id": room_id, "message": "기존 채팅방 입장"}

    # (4) 방이 없으면 -> 새로 만들고 번호를 줍니다. [cite: 6]
    # nextval('talk_room_id_s')는 번호표 뽑는 기계입니다.
    create_room_sql = text("""
        INSERT INTO multicampus_schema.talk_room (
            talk_room_id, member_no1, member_no2, create_user
        ) VALUES (
            nextval('multicampus_schema.talk_room_id_s'), :m1, :m2, :creator
        ) RETURNING talk_room_id
    """)
    
    try:
        new_room_id = db.execute(create_room_sql, {
            "m1": my_no, "m2": target_no, "creator": req.my_id
        }).scalar()
        db.commit()
        return {"room_id": new_room_id, "message": "새 채팅방 생성 완료"}
    except Exception as e:
        db.rollback()
        print(f"방 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="채팅방 생성 실패")

# 3. 📜 내 채팅 목록 가져오기 (이게 곧 친구 목록!)
# "나랑 대화 중인 사람"만 보여줍니다.
@router.get("/list")
def get_my_rooms(user_id: str, db: Session = Depends(get_db)):
    # 내 번호 조회
    my_no_sql = text("SELECT member_no FROM multicampus_schema.member WHERE member_id = :id")
    my_no = db.execute(my_no_sql, {"id": user_id}).scalar()

    # :my_no 부분만 파라미터로 바꿨습니다.
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