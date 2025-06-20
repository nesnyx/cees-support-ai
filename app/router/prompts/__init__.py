from fastapi import APIRouter, HTTPException,Depends, Request,status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.service.authentication.models import User
from app.service.authentication import get_current_user,verify_cookie
from app.router.prompts.model import PromptInput
from app.service.database.prompt import create_update_prompt, get_prompt
from config.mysql import get_db
import uuid
import os
import logging

router_prompts = APIRouter(prefix="/prompts")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router_prompts.get("/get-by-id")
async def get_by_id(request : Request,current_user = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    prompt = await get_prompt(current_user['id'],db)
    if prompt['status'] == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="prompt doesnt exist")
    return prompt


@router_prompts.put("/create")
async def create(input : PromptInput,current_user = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    try:
        prompt = await create_update_prompt(current_user['id'],input.system_template,db)
        if prompt['status'] == False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="persoalan mendalam")
        return prompt
    except Exception as e:
        logging.info(f"Error Message : {e} ")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Error")
