"""채팅 관련 API 엔드포인트

친구 검색, 채팅방 생성/조회, 대화 내역 조회 기능 제공
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from typing import Optional

from app.core.database import get_db
from app.api.schemas import RoomResponse, RoomCreateRequest
from app.services.chat_service import ChatService

router = APIRouter()


@router.get("/search")
def search_user(
    my_id: str,
    name: Optional[str] = None,
    member_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """친구 검색 (이름 또는 아이디)"""
    return ChatService.search_users(db, my_id, name, member_id)


@router.post("/room", response_model=RoomResponse)
def get_or_create_room(req: RoomCreateRequest, db: Session = Depends(get_db)):
    """채팅방 생성 또는 기존 방 조회"""
    return ChatService.create_or_get_room(db, req.my_id, req.target_id)


@router.get("/list")
def get_my_rooms(user_id: str, db: Session = Depends(get_db)):
    """내 채팅방 목록 조회"""
    return ChatService.get_my_rooms(db, user_id)


@router.get("/history/{room_id}")
def get_chat_history(room_id: int, db: Session = Depends(get_db)):
    """채팅방 대화 내역 조회"""
    return ChatService.get_chat_history(db, room_id)

# 잠시 추가 (소영)
@router.get("/debug/word")
def debug_word(word: str, db: Session = Depends(get_db)):
    exact = db.execute(
        text("""
            SELECT word_name, url_path
            FROM multicampus_schema.corpus
            WHERE word_name = :word
            LIMIT 20
        """),
        {"word": word},
    ).fetchall()

    like = db.execute(
        text("""
            SELECT word_name, url_path
            FROM multicampus_schema.corpus
            WHERE word_name LIKE :pattern
            LIMIT 50
        """),
        {"pattern": f"%{word}%"},
    ).fetchall()

    return {
        "word": word,
        "counts": {"exact": len(exact), "like": len(like)},
        "exact": [{"word_name": r[0], "url_path": r[1]} for r in exact],
        "like": [{"word_name": r[0], "url_path": r[1]} for r in like],
    }

