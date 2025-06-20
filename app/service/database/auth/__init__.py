from config.mysql import get_db
from utils.security import get_password_hash,verify_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class Auth:
    def __init__(self,username : str, password : str, db : AsyncSession):
        self.username = username
        self.password = password
        self.db = db
    async def login(self):
        query = text("SELECT id, username,hash FROM accounts WHERE username = :username")
        check_account =  await self.db.execute(query, {
            "username" : self.username
        })
        account_data = check_account.mappings().first()
        print(f"account data : {account_data}")
        if not account_data:
            return {"status": False, "detail": "Username atau password salah"}

        if not verify_password(self.password, account_data['hash']):
            return {"status": False, "detail": "Username atau password salah"}
        return {"status": True, "data": {"id": account_data['id'], "username": account_data['username']}}

    async def register(self):
        hashed_password = get_password_hash(self.password)
        query = text("INSERT INTO accounts(username, hash, password) VALUES (:username, :hash, :password )")
        try:
            await self.db.execute(query,{
            "username" : self.username,
            "hash" : hashed_password,
            "password": self.password
            })
            await self.db.commit()
            return {"status" : True}
        except Exception as e:
            print(f"Error Database : {e} ")
            await self.db.rollback()
            return {"status" : False}