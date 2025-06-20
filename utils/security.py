from cryptography.fernet import Fernet
import base64
import os
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Generate a key or load existing one
key = Fernet.generate_key()
f = Fernet(key)

def encrypt_cookie(cookie):
    return f.encrypt(cookie.encode())
def decrypt_cookie(cookie): 
    return f.decrypt(cookie).decode()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)