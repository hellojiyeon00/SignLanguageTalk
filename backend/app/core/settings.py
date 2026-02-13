# """
# DB 접속 거치지 않고 DEV용으로 우회해서 모델 서버 연결 테스트 진행함 (소영)
# """
# # app/core/settings.py
# import os

# ENV = os.getenv("ENV", "dev")
# AUTH_MODE = "stub" if ENV == "dev" else "db"
