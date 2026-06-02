from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
TURSO_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
elif TURSO_URL:
    import libsql_experimental as libsql
    engine = create_engine(
        "sqlite+libsql:///",
        creator=lambda: libsql.connect(
            database=TURSO_URL,
            auth_token=TURSO_TOKEN
        ),
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        "sqlite:///./skillforge.db",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()