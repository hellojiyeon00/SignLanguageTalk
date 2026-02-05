# app/main.py
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    room = data.get("room")
    sender = data.get("username")
    msg = data.get("message")
    
    # 데이터가 비어있는지 확인
    print(f"📩 메시지 수신: [{room}] {sender}: {msg}")
    
    if room and sender and msg:
        await sio.emit("receive_message", {
            "sender": sender,
            "message": msg
        }, room=room)
    else:
        print("⚠️ 잘못된 데이터 수신!")