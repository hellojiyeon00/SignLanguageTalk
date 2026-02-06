# backend/app/core/config.py

# ==============================================================================
# 1. 라이브러리 임포트
# ==============================================================================
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    [환경 설정 관리자]
    프로젝트 최상위 폴더에 있는 .env 파일을 읽어서,
    DB 접속 정보나 보안 키 같은 중요한 설정들을 파이썬 변수로 변환해줍니다.
    """

    # ==========================================================================
    # 2. 필수 환경 변수 정의
    # .env 파일에 이 변수들이 없으면 서버가 켜지지 않습니다. (실수 방지)
    # ==========================================================================
    DB_USER: str      # 데이터베이스 아이디
    DB_PASSWORD: str  # 데이터베이스 비밀번호
    DB_HOST: str      # 데이터베이스 주소 (예: localhost)
    DB_PORT: str      # 데이터베이스 포트 (예: 5432)
    DB_NAME: str      # 데이터베이스 이름
    
    SECRET_KEY: str   # 보안 토큰 생성용 비밀키
    ALGORITHM: str = "HS256" # 암호화 알고리즘 (기본값 HS256)

    # ==========================================================================
    # 3. DB 접속 URL 자동 생성
    # 정보를 조립해서 SQLAlchemy가 사용할 접속 주소를 만들어줍니다.
    # ==========================================================================
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ==========================================================================
    # 4. .env 파일 경로 찾기 (핵심 로직)
    # 현재 파일 위치(backend/app/core/config.py)를 기준으로
    # 4단계 위로 올라가서 최상위 폴더(project/)의 .env를 찾습니다.
    # ==========================================================================
    
    # 1) 현재 파일의 절대 경로: .../project/backend/app/core/config.py
    _current_file_path = os.path.abspath(__file__)
    
    # 2) 상위 폴더로 이동하며 경로 추적
    _core_dir = os.path.dirname(_current_file_path)       # .../project/backend/app/core
    _app_dir = os.path.dirname(_core_dir)                 # .../project/backend/app
    _backend_dir = os.path.dirname(_app_dir)              # .../project/backend
    
    # 3) 최종 목표: 프로젝트 최상위 폴더
    _project_root = os.path.dirname(_backend_dir)         # .../project (여기에 .env가 있음!)
    
    # 4) .env 파일의 최종 경로 완성
    _env_file_path = os.path.join(_project_root, ".env")

    # ==========================================================================
    # 5. 설정 적용 (Pydantic V2 문법)
    # 위에서 계산한 경로(_env_file_path)를 사용하여 설정을 불러옵니다.
    # ==========================================================================
    model_config = SettingsConfigDict(
        env_file=_env_file_path,     # 계산된 경로의 파일을 읽음
        env_file_encoding="utf-8",   # 한글 깨짐 방지
        extra="ignore"               # .env에 불필요한 변수가 있어도 에러 안 냄
    )

# 설정 객체 생성 (이제 어디서든 settings.DB_USER 처럼 사용 가능)
settings = Settings()