
from utils.security import get_password_hash,verify_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class Auth:
    def __init__(self,username : str, password : str, db : AsyncSession):
        self.username = username
        self.password = password
        self.db = db
    async def login(self):
        query = text("SELECT a.id, a.username,a.hash,pt.system_template FROM accounts a INNER JOIN prompt_template pt ON pt.user_id = a.id WHERE a.username = :username")
        check_account =  await self.db.execute(query, {
            "username" : self.username
        })
        account_data = check_account.mappings().first()
        print(f"account data : {account_data}")
        if not account_data:
            return {"status": False, "detail": "Username atau password salah"}

        if not verify_password(self.password, account_data['hash']):
            return {"status": False, "detail": "Username atau password salah"}
        return {"status": True, "data": {"id": account_data['id'], "username": account_data['username'], 'prompt':account_data['system_template']}}

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
        


async def get_prompt_template(id : str,db : AsyncSession):
        query = text("SELECT system_template FROM prompt_template WHERE user_id = :id")
        get_template =  await db.execute(query, {
            "id" : id
        })
        template = get_template.mappings().first()
        print(template)
        if not template:
            return {"status": False, "detail": "Tidak ditemukan system template"}
        return {"status": True, "data": {"prompt":template['system_template']}}