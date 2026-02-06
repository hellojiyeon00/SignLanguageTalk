# backend/app/api/chat.py

# ==============================================================================
# 1. 라이브러리 및 모듈 임포트
# ==============================================================================
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional # 선택적 매개변수(값이 없어도 되는 변수)를 위해 사용
from pydantic import BaseModel

# 우리가 만든 모듈들 가져오기
from app.core.database import get_db # DB 세션 생성기
# schemas.py에서 정의한 '방 번호 응답(RoomResponse)'과 '방 생성 요청(RoomCreateRequest)' 양식을 가져옵니다.
from app.api.schemas import RoomResponse, RoomCreateRequest 
# 실제 채팅 관련 비즈니스 로직(DB 작업 등)을 수행할 서비스 클래스입니다.
from app.services.chat_service import ChatService 

# APIRouter 객체 생성 (URL 경로 관리를 담당)
router = APIRouter()

# ==============================================================================
# 2. 친구 검색 API (GET /search)
# ==============================================================================
@router.get("/search")
def search_user(
    my_id: str, # 검색을 요청하는 사람의 아이디 (나 자신은 검색 결과에서 빼야 하므로 필요)
    name: Optional[str] = None,      # 검색할 이름 (선택 사항: 안 넣으면 None)
    member_id: Optional[str] = None, # 검색할 아이디 (선택 사항: 안 넣으면 None)
    db: Session = Depends(get_db)    # DB 연결 세션 주입
):
    """
    [친구 검색 엔드포인트]
    사용자의 이름이나 아이디 일부를 입력받아, 해당하는 친구 목록을 찾아줍니다.
    예: /chat/search?my_id=hoyong&name=김
    """
    
    # [서비스 위임]
    # "DB에서 이 이름(name)이나 아이디(member_id)를 가진 사람 좀 찾아줘. 단, 나는(my_id) 빼고!"
    # 검색 로직은 전적으로 ChatService가 담당합니다.
    return ChatService.search_users(db, my_id, name, member_id)

# ==============================================================================
# 3. 채팅방 생성 또는 입장 API (POST /room)
# ==============================================================================
@router.post(
    "/room", 
    response_model=RoomResponse # 성공 시 RoomResponse 양식(room_id, message)으로 응답한다고 선언
)
def get_or_create_room(
    req: RoomCreateRequest,    # 요청 본문(Body) 데이터: { "my_id": "...", "target_id": "..." }
    db: Session = Depends(get_db)
):
    """
    [채팅방 생성/입장 엔드포인트]
    나(my_id)와 상대방(target_id)이 대화할 방을 요청합니다.
    1. 이미 둘 사이에 방이 있다면? -> 기존 방 번호를 반환 (입장)
    2. 방이 없다면? -> 새 방을 만들고 그 번호를 반환 (생성)
    """
    
    # [서비스 위임]
    # "나랑 쟤랑 대화할 건데 방 좀 잡아줘." (없으면 만들어서라도 가져옴)
    # ChatService.create_or_get_room 함수가 {room_id: 1, message: "..."} 형태의 딕셔너리를 반환합니다.
    # 이 딕셔너리는 위의 response_model=RoomResponse 덕분에 자동으로 검증되고 문서화됩니다.
    return ChatService.create_or_get_room(db, req.my_id, req.target_id)

# ==============================================================================
# 4. 내 채팅방 목록 조회 API (GET /list)
# ==============================================================================
@router.get("/list")
def get_my_rooms(
    user_id: str,                 # 목록을 조회할 사용자의 아이디
    db: Session = Depends(get_db)
):
    """
    [채팅방 목록 엔드포인트]
    내가 참여하고 있는 모든 채팅방(=대화 중인 친구들) 목록을 가져옵니다.
    """
    
    # [서비스 위임]
    # "내가 속한 방 리스트랑, 거기 있는 상대방 이름들 좀 뽑아줘."
    # 복잡한 JOIN 쿼리나 UNION 연산은 모두 Service 계층 안에서 처리됩니다.
    return ChatService.get_my_rooms(db, user_id)

# ==============================================================================
# 5. 과거 대화 내역 조회 API (GET /history/{room_id})
# ==============================================================================
@router.get("/history/{room_id}")
def get_chat_history(
    room_id: int,                 # URL 경로에 포함된 방 번호 (예: /chat/history/1)
    db: Session = Depends(get_db)
):
    """
    [대화 내역 엔드포인트]
    특정 채팅방(room_id)에 들어갔을 때, 과거에 나눴던 대화 내용들을 시간순으로 불러옵니다.
    """
    
    # [서비스 위임]
    # "1번 방에서 오고 간 대화 내용 싹 다 긁어와."
    return ChatService.get_chat_history(db, room_id)