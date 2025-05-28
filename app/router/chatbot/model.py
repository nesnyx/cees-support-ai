from pydantic import BaseModel


class ChatInput(BaseModel):
    question : str


class WhatsappInput(BaseModel):
    question : str
    session_id:str