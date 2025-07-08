from pydantic import BaseModel

from typing import Dict, Any, Optional

class ChatInput(BaseModel):
    input : str


class WhatsappInput(BaseModel):
    question : str
    session_id:str
    
    


class RAGRequest(BaseModel):
    user: Dict[str, Any]
    prompt: str
    telp_customer: str
    question: str

class RAGResponse(BaseModel):
    response: str
    intent: Dict[str, Any]
    session_id: str
    context_length: int
    status: str
    processing_mode: Optional[str] = "langgraph"
