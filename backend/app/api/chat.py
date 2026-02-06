# backend/app/api/chat.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.services.chat_service import ChatService # 서비스 임포트

router = APIRouter()

class RoomCreateRequest(BaseModel):
    my_id: str
    target_id: str

@router.get("/search")
def search_user(
    my_id: str, 
    name: Optional[str] = None, 
    member_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    return ChatService.search_users(db, my_id, name, member_id)

@router.post("/room")
def get_or_create_room(req: RoomCreateRequest, db: Session = Depends(get_db)):
    return ChatService.create_or_get_room(db, req.my_id, req.target_id)

@router.get("/list")
def get_my_rooms(user_id: str, db: Session = Depends(get_db)):
    return ChatService.get_my_rooms(db, user_id)

@router.get("/history/{room_id}")
def get_chat_history(room_id: int, db: Session = Depends(get_db)):
    return ChatService.get_chat_history(db, room_id)