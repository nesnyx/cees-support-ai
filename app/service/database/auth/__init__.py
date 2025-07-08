
from utils.security import get_password_hash,verify_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class Auth:
    def __init__(self,username, password , db : AsyncSession):
        self.username = username
        self.password = password
        self.db = db
    async def login(self):
        # Query ambil akun berdasarkan username
        query = text("SELECT id, username, hash FROM accounts WHERE username = :username")
        check_account = await self.db.execute(query, {
            "username": self.username
        })
        account_data = check_account.mappings().first()
        print(f"account data : {account_data}")

        # Cek apakah akun ditemukan
        if not account_data:
            return {"status": False, "detail": "Username atau password salah"}

        # Verifikasi password
        if not verify_password(self.password, account_data['hash']):
            return {"status": False, "detail": "Username atau password salah"}

        # Query untuk ambil template prompt jika ada
        query_template = text("""
            SELECT pt.system_template 
            FROM prompts pt 
            WHERE pt.user_id = :user_id
        """)
        check_template = await self.db.execute(query_template, {
            "user_id": account_data['id']
        })
        prompt_template = check_template.mappings().first()

        return {
            "status": True,
            "data": {
                "id": account_data['id'],
                "username": account_data['username'],
                "prompt": prompt_template['system_template'] if prompt_template else [None]
            }
        }


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