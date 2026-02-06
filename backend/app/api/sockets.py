# backend/app/api/sockets.py

# ==============================================================================
# 1. 라이브러리 임포트
# ==============================================================================
import socketio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from fastapi.concurrency import run_in_threadpool 

from app.core.database import SessionLocal

# ==============================================================================
# 2. 로거(Logger) 설정
# print() 대신 시스템 로그를 남기기 위한 설정입니다.
# ==============================================================================
logger = logging.getLogger("socket") # 'socket'이라는 이름표를 단 로거 생성
logging.basicConfig(level=logging.INFO) # INFO 레벨(일반 정보)부터 출력

# ==============================================================================
# 3. Socket.IO 서버 생성
# ==============================================================================
# main.py에서 FastAPI 앱에 씌울 알맹이(sio) 객체입니다.
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")

# ==============================================================================
# 4. 이벤트 핸들러 (Event Handlers)
# ==============================================================================

@sio.event
async def connect(sid, environ):
    """
    [이벤트: 접속]
    클라이언트가 소켓 서버에 연결되었을 때 호출됩니다.
    """
    logger.info(f"✅ [Socket] 접속됨 | SID: {sid}")

@sio.on("join_room")
async def handle_join_room(sid, data):
    """
    [이벤트: 방 입장]
    사용자를 특정 채팅방 그룹(Room)에 추가하여 메시지를 받을 수 있게 합니다.
    """
    room = data.get("room")
    username = data.get("username")
    
    if room and username:
        await sio.enter_room(sid, room)
        logger.info(f"🚪 [입장] {username} -> {room}")

@sio.on("leave_room")
async def handle_leave_room(sid, data):
    """
    [이벤트: 방 퇴장]
    사용자를 채팅방 그룹에서 제외합니다.
    """
    room = data.get("room")
    username = data.get("username")
    
    if room:
        await sio.leave_room(sid, room)
        logger.info(f"👋 [퇴장] {username} <- {room}")

# ==============================================================================
# 5. DB 저장 함수 (동기 방식)
# ==============================================================================
def save_message_sync(room_id: int, sender_id: str, msg: str):
    """
    [동기 함수] 채팅 메시지를 DB에 저장합니다.
    - 이 함수는 'run_in_threadpool'을 통해 별도 스레드에서 실행됩니다.
    - 반환값: 보낸 사람의 이름 (DB에 저장된 full_name)
    """
    db = SessionLocal()
    try:
        # 1. 사용자 정보 조회 (아이디 -> 번호, 이름)
        get_user_sql = text("SELECT member_no, full_name FROM multicampus_schema.member WHERE member_id = :id")
        user_info = db.execute(get_user_sql, {"id": sender_id}).fetchone()
        
        if not user_info:
            logger.warning(f"⚠️ [DB 저장 실패] 존재하지 않는 사용자: {sender_id}")
            return None

        member_no, sender_name = user_info[0], user_info[1]

        # 2. 메시지 INSERT
        # DB에는 'Asia/Seoul' 타임존으로 현재 시간을 저장합니다.
        insert_sql = text("""
            INSERT INTO multicampus_schema.talk (
                talk_room_id, member_no, talk_date, message, create_user
            ) VALUES (
                :r_id, :m_no, CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Seoul', :msg, :c_user
            )
        """)
        
        db.execute(insert_sql, {
            "r_id": room_id,
            "m_no": member_no,
            "msg": msg,
            "c_user": sender_id
        })
        db.commit()
        
        return sender_name # 성공 시 이름 반환

    except Exception as e:
        logger.error(f"❌ [DB 에러] 메시지 저장 실패: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

# ==============================================================================
# 6. 메시지 전송 이벤트 (비동기)
# ==============================================================================
@sio.on("send_message")
async def handle_send_message(sid, data):
    """
    [이벤트: 메시지 전송]
    1. 클라이언트로부터 메시지를 수신합니다.
    2. DB에 비동기(Threadpool)로 저장합니다.
    3. 같은 방에 있는 모든 사용자에게 메시지를 브로드캐스팅(emit)합니다.
    """
    room_id = data.get("room_id")
    room_name = data.get("room")
    sender_id = data.get("username")
    msg = data.get("message")

    # [시간 보정] 한국 시간(KST) 구하기 (UTC+9)
    # 서버 시간이 UTC여도 항상 한국 시간을 표시하기 위함입니다.
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST).strftime("%H:%M")

    if room_id and sender_id and msg:
        try:
            # 1. DB 저장 (별도 스레드에서 실행)
            sender_name = await run_in_threadpool(save_message_sync, room_id, sender_id, msg)
            
            # 2. 실시간 전송 (DB 저장 성공 시에만)
            if sender_name:
                payload = {
                    "sender": sender_id,
                    "sender_name": sender_name,
                    "message": msg,
                    "time": now_kst # 한국 시간 전송
                }
                
                # 해당 방(room_name)에 있는 모든 사람에게 발송
                await sio.emit("receive_message", payload, room=room_name)
                
        except Exception as e:
            logger.error(f"❌ [소켓 에러] 메시지 처리 실패: {e}")