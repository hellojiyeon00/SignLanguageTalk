# app/main.py
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from sqlalchemy import text

from app.core.database import SessionLocal
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")
app = FastAPI()
sio_app = socketio.ASGIApp(sio, app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(chat_router, prefix="/chat")

@sio.event
async def connect(sid, environ):
    print(f"✅ 접속: {sid}")

@sio.on("join_room")
async def handle_join_room(sid, data):
    room = data.get("room")
    username = data.get("username")
    print(f"🚪 입장 시도: {username} -> {room}") # 서버 터미널에 찍힘
    
    await sio.enter_room(sid, room)
    print(f"🚪 {username}님이 {room} 방에 입장했습니다.")
    
@sio.on("leave_room")
async def handle_leave_room(sid, data):
    room = data.get("room")
    username = data.get("username")
    if room:
        await sio.leave_room(sid, room) # 서버에서 방 퇴장 처리
        print(f"🚪 {username}님이 {room} 방에서 나갔습니다.")

@sio.on("send_message")
async def handle_send_message(sid, data):
    
    room_id = data.get("room_id") # 숫자로 된 방 ID
    room_name = data.get("room")   # 소켓 통신용 이름 (ID_ID)
    sender_id = data.get("username") # 보낸 사람의 아이디 (문자)
    msg = data.get("message")
    
    now = datetime.now().strftime("%H:%M")
    
    if room_id and sender_id and msg:
        db = SessionLocal()
        try:
            # [수정] 성명(full_name)도 같이 가져옵니다.
            get_user = text("SELECT member_no, full_name FROM multicampus_schema.member WHERE member_id = :id")
            user_info = db.execute(get_user, {"id": sender_id}).fetchone()
            member_no, sender_name = user_info[0], user_info[1]

            # 2.  정의서 구조대로 talk 테이블에 저장
            insert_talk = text("""
                INSERT INTO multicampus_schema.talk (
                    talk_room_id, member_no, talk_date, message, create_user
                ) VALUES (
                    :r_id, :m_no, CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Seoul', :msg, :c_user
                )
            """)
            db.execute(insert_talk, {
                "r_id": room_id, 
                "m_no": member_no, 
                "msg": msg, 
                "c_user": sender_id
            })
            db.commit() # 저장 완료!
        except Exception as e:
            print(f"❌ 저장 실패: {e}")
            db.rollback()
        finally:
            db.close()
        
        await sio.emit("receive_message", {
                "sender": sender_id,
                "sender_name": sender_name, # [추가]
                "message": msg,
                "time": datetime.now().strftime("%H:%M")
        }, room=room_name)