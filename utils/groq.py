from langchain_groq.chat_models import ChatGroq
from dotenv import load_dotenv
import os
load_dotenv()

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0.7,
    api_key= os.getenv("GROQ_API_KEY")
)
