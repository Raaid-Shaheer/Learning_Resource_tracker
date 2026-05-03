import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from backend.schemas import TokenData
from dotenv import load_dotenv
load_dotenv()

# --- Config ---
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Password context: tells passlib to use bcrypt ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    
    hashed_password = pwd_context.hash(plain)
    return hashed_password


def verify_password(plain: str, hashed: str) -> bool:
   
    verified = pwd_context.verify(plain,hashed)
    return verified


def create_access_token(data: dict) -> str:
    # 1. Copy data so you don't mutate the original
    # 2. Calculate expiry: now (UTC) + ACCESS_TOKEN_EXPIRE_MINUTES
    # 3. Add "exp" key to the copy
    # 4. Encode with jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    # 5. Return the token string
    data_copy = data.copy()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data_copy["exp"] = expiry
    token =jwt.encode(data_copy,SECRET_KEY,algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> TokenData | None:
    # 1. Try jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # 2. Pull user_id and role out of the payload
    # 3. Return a TokenData(user_id=..., role=...)
    # 4. If JWTError is raised, return None
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        user_id = payload["user_id"]
        role = payload["role"]
        return TokenData(user_id=user_id, role=role)
    except JWTError as e:
        return None
