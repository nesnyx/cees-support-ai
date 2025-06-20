import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status,Request
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt
from config.db import db
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}, 
)
# Konteks untuk hashing password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Skema OAuth2, `tokenUrl` menunjuk ke endpoint login kita
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/authentication/login")

# --- Fungsi Helper untuk Password ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi password plain dengan hash-nya."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Membuat hash dari password."""
    return pwd_context.hash(password)

# --- Fungsi untuk JWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Membuat access token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=120)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


# --- Dependency Utama untuk Otentikasi ---

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency untuk memvalidasi token dan mendapatkan data pengguna.
    Ini yang akan digunakan untuk memproteksi endpoint.
    """
    # cookies = request.cookies.get("session_user")
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        userId : int = payload.get("id")
        if username is None or userId is None:
            raise credentials_exception
        return {"username": username, "id" : userId} 
    except JWTError:
        raise credentials_exception


async def verify_cookie(request: Request):
    token = request.cookies.get("session_user")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        userId : int = payload.get("id")
        if username is None or userId is None:
            raise credentials_exception
        return {"username": username, "id" : userId} 
    except JWTError:
        raise credentials_exception


async def get_user_by_id(db : AsyncSession,user_id :str ):
    query = text("SELECT id,username FROM accounts WHERE id = :user_id")
    try:
        get_user = await db.execute(query, {
            "user_id" : user_id
        })
        row = get_user.mappings().all()
        if not row:
            return {"data" : {},"status":False}
        return {"data" : row,"status":True}
    except Exception as e:
        print(f"Error database : {e}")
        await db.rollback()
        return {"status": False, "id": None, "error": str(e)}


class AccountService:
    def __init__(self,username = "", password = ""):
        self.username = username
        self.password = password
        self.db = db
    
    def register(self):
        try:
            hash = get_password_hash(password=self.password)
            account = self.db.account.register(self.username, self.password,hash)
            print(account)
            return {
                "status":True,
                "data":account
            }
        except Exception as e:
            print(f"Database query error: {e}")
            return {
                "status":False,
            }

    def get_by_username(self):
        try:
            account = self.db.account.get_by_username(self.username)
            return {
                "status":True,
                "data":account
            }
        except Exception as e:
            print(f"Database query error: {e}")
            return {
                "status":False,
            }