from pydantic import BaseModel


class ChatInput(BaseModel):
    input : str


class WhatsappInput(BaseModel):
    question : str
    session_id:str