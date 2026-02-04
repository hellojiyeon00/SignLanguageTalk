from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# 1. 엔진 생성
engine = create_engine(settings.DATABASE_URL)

# 2. 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 모델들의 조상님
Base = declarative_base()

# 4. 세션 배달부 (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()