from fastapi import APIRouter, status, Depends, Request, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from app.router.chatbot.model import ChatInput
from app.service.agent.langgraph_agent import ai_agent
from app.service.authentication import get_user_by_id
from config.postgresql import get_db
from app.service.database.prompt import get_prompt
from sqlalchemy.ext.asyncio import AsyncSession
import logging


router_chat = APIRouter(prefix="/chat")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router_chat.post("/interect")
async def langgraph_agent_endpoint(
    request: Request,
    input_data: ChatInput,
    user_id: str = Query(...),
    telp_customer: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    AI Agent endpoint menggunakan LangGraph create_react_agent
    """
    try:
        check_user = await get_user_by_id(db, user_id)
        if check_user["status"] == False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="user doesnt exist"
            )

        get_prompt_by_user_id = await get_prompt(user_id, db)
        if get_prompt_by_user_id["status"] == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="prompt doesnt exist"
            )

        prompt = get_prompt_by_user_id["data"][0]["system_template"]
        # Process dengan AI Agent
        result = await ai_agent.process_query(
            user=check_user["data"][0],
            prompt=prompt,
            telp_customer=telp_customer,
            question=input_data.input,
        )

        logger.info(f"AI Agent query processed for user {user_id}")

        return {"data": result, "message": "Processed by LangGraph AI Agent"}

    except Exception as e:
        logger.error(f"AI Agent query failed: {e}")

        return JSONResponse(
            status_code=500,
            content={
                "error": "AI Agent processing failed",
                "detail": str(e),
                "agent_type": "langgraph_react_agent",
            },
        )


# @router_chat.post("/interect/testing")
# async def ai_agent(input_data : ChatInput,request : Request, user_id:str,telp_customer:str,db: AsyncSession = Depends(get_db)):
#     check_user = await get_user_by_id(db,user_id)
#     if check_user['status'] == False:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user doesnt exist")
#     get_prompt_by_user_id = await get_prompt(user_id,db)
#     if get_prompt_by_user_id['status'] == False:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="prompt doesnt exist")
#     user_persona = get_prompt_by_user_id['data'][0]['system_template']
#     result = perform_agentic_query(user_id=user_id,telp_customer=telp_customer,question=input_data.input,user_persona=user_persona)
#     return {
#         "data": result,
#         "message": "success"
#     }
