from config.mysql import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid

class Prompt:
    def __init__(self,user_id : str, prompt_id : str,system_template:str ,db : AsyncSession):
        self.user_id = user_id
        self.prompt_id = prompt_id
        self.system_tempalte = system_template
        self.db = db



async def create_update_prompt(user_id : str, system_template,db : AsyncSession):
        new_prompt_id = str(uuid.uuid4())
        query_select = text("SELECT id, user_id, system_template FROM prompt_template WHERE user_id = :user_id")
        query_insert = text("INSERT INTO prompt_template(id, system_template, user_id) VALUES (:id,:system_template, :user_id)")
        query_update = text("UPDATE prompt_template SET system_template = :system_template WHERE user_id = :user_id")
        try:
            check_template =  await db.execute(query_select, {
                "user_id" : user_id
            })
            row = check_template.fetchone()
            if not row:
                await db.execute(query_insert,{
                    "id":new_prompt_id,
                    "system_template":system_template,
                    "user_id": user_id
                })   
                await db.commit()
                return {"status": True, "id": new_prompt_id, "msg":"berhasil dibuat"}
            
            await db.execute(query_update, {
                "system_template" : system_template,
                "user_id" : user_id
            })
            await db.commit()
            return {"status": True, "msg":"berhasil diupdate"}
        except Exception as e:
            print(f"Error database : {e}")
            await db.rollback()
            return {"status": False, "id": None, "error": str(e)}


async def create_prompt(user_id : str,system_template:str ,db : AsyncSession):
        new_prompt_id = str(uuid.uuid4())
        query = text("INSERT INTO prompt_template(id, system_template, user_id) VALUES (:id,:system_template, :user_id) ")
        try:
            await db.execute(query,{
                "id":new_prompt_id,
                "system_template":system_template,
                "user_id": user_id
            })   
            await db.commit()
            return {"status": True, "id": new_prompt_id}
            
        except Exception as e:
            print(f"Error database : {e}")
            await db.rollback()
            return {"status": False, "id": None, "error": str(e)}

async def get_prompt(user_id : str ,db : AsyncSession):
        query = text("SELECT id, user_id, system_template FROM prompt_template WHERE user_id = :user_id")
        check_template =  await db.execute(query, {
            "user_id" : user_id
        })
        row = check_template.mappings().all()
        if not row:
            return {"data" : {},"status":False}
        return {"data" : row,"status":True}
