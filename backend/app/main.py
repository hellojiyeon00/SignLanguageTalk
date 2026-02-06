# backend/app/main.py

# ==============================================================================
# 1. 라이브러리 및 모듈 임포트
# ==============================================================================
import socketio # Socket.IO 서버를 만들기 위한 라이브러리
from fastapi import FastAPI # 웹 프레임워크
from fastapi.middleware.cors import CORSMiddleware # 보안(CORS) 설정을 위한 도구

# 우리가 만든 API 라우터(웨이터)들을 가져옵니다.
from app.api.auth import router as auth_router # 로그인, 회원가입 담당
from app.api.chat import router as chat_router # 채팅, 친구검색 담당

# [핵심] 소켓 통신을 전담하는 'sockets.py'에서 알맹이(sio) 객체를 가져옵니다.
# main.py는 소켓 로직을 직접 구현하지 않고, 연결만 시켜주는 역할을 합니다.
from app.api.sockets import sio

# ==============================================================================
# 2. FastAPI 앱 생성
# ==============================================================================
# FastAPI 객체를 생성합니다. 이 객체가 웹 서버의 본체가 됩니다.
app = FastAPI()

# ==============================================================================
# 3. CORS 미들웨어 설정 (보안)
# ==============================================================================
# 웹 브라우저(프론트엔드)가 다른 주소의 서버(백엔드)로 접속할 때 발생하는 
# 보안 경고(CORS 에러)를 해제합니다.
# allow_origins=["*"]: "누구든지 내 서버에 접속해도 좋아!" (개발 편의를 위해 모든 접속 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 4. 라우터 등록 (Router)
# ==============================================================================
# 만들어둔 기능들을 서버에 부착합니다.

# auth_router: "/auth" 로 시작하는 모든 요청을 처리합니다.
# 예: http://localhost:8000/auth/login, /auth/signup
app.include_router(auth_router, prefix="/auth")

# chat_router: "/chat" 로 시작하는 모든 요청을 처리합니다.
# 예: http://localhost:8000/chat/search, /chat/list
app.include_router(chat_router, prefix="/chat")

# ==============================================================================
# 5. Socket.IO 통합 (Wrapping)
# ==============================================================================
# [매우 중요]
# FastAPI 앱(app)을 Socket.IO 앱(ASGIApp)으로 감싸버립니다.
# 이렇게 하면 서버로 들어오는 요청 중:
# 1. "/socket.io" 로 시작하는 요청 -> sio가 가로채서 처리 (실시간 통신)
# 2. 나머지 일반 요청 -> 원래의 FastAPI app으로 전달 (로그인, 채팅목록 등)

app = socketio.ASGIApp(sio, app)

