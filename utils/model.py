from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv("API_KEY")
llm = ChatGoogleGenerativeAI(api_key=API_KEY, model="gemini-2.0-flash")
EMBEDDING_MODEL = "models/embedding-001"