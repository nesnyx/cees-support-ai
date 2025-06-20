from fastapi import APIRouter,status,Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from app.router.chatbot.model import ChatInput
from app.service.rag_service import perform_rag_query
from app.service.authentication import get_current_user,verify_cookie,get_user_by_id
from config.mysql import get_db
from app.service.database.prompt import get_prompt
from sqlalchemy.ext.asyncio import AsyncSession
import logging


router_chat = APIRouter(prefix="/chat")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@router_chat.post("/interect")
async def interect_chatbot(input_data : ChatInput,request : Request,user_id:str,db: AsyncSession = Depends(get_db)):
    try:
        check_user = await get_user_by_id(db,user_id)
        print(f"check_user : {check_user['data'][0]}")
        if check_user['status'] == False:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user doesnt exist")
        get_prompt_by_user_id = await get_prompt(user_id,db)
        print(get_prompt_by_user_id['data'][0]['system_template'])
        if get_prompt_by_user_id['status'] == False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="prompt doesnt exist")
        prompt = get_prompt_by_user_id['data'][0]['system_template']
        chatbot = perform_rag_query(check_user['data'][0],prompt,input_data.input)
        return {
            "msg":chatbot
        }
    except Exception as e:
        logging.info(f"Error Message : {e} ")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"{e}")





