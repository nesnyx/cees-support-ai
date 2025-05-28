from fastapi import APIRouter,status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from app.router.chatbot.model import ChatInput, WhatsappInput
from app.service.chatbot import ChatBotService,system_template
from utils.extracted_format import extract_response_and_json
from utils.model import llm
import uuid, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
session_id = str(uuid.uuid4())

router_chatbot = APIRouter(prefix="/chat")

@router_chatbot.post("/interect")
async def interect(input: ChatInput):
    try:
        chatbot = ChatBotService(system_template=system_template,session_id=session_id, llm=llm,question=input.question)
        response = chatbot.chain_with_story()
        response_text, structured_data = extract_response_and_json(response)
        logger.info(f"Response to user: {response_text}")
        logger.info(f"Structured JSON: {structured_data}")
        logger.info(f"Response: {response}")
        return JSONResponse(status_code=status.HTTP_200_OK, content={
            "response":response_text, "session_id":chatbot.session_id, "metadata":structured_data
        })
    except Exception as e:
        logging.info(f"Error Message : {e} ")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Error")
    

@router_chatbot.post("/wa/interect")
async def wa(input : WhatsappInput):
    try:
        chatbot = ChatBotService(system_template=system_template,session_id=input.session_id, llm=llm,question=input.question)
        response = chatbot.chain_with_story()
        response_text, structured_data = extract_response_and_json(response)
        logger.info(f"Response to user: {response_text}")
        logger.info(f"Structured JSON: {structured_data}")
        logger.info(f"Response: {response}")
        return JSONResponse(status_code=status.HTTP_200_OK, content={
            "response":response_text, "session_id":chatbot.session_id, "metadata":structured_data
        })
    except Exception as e:
        logging.info(f"Error Message : {e} ")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Error")