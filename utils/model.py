from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from dotenv import load_dotenv
import os
load_dotenv()

# set_llm_cache(InMemoryCache())

API_KEY = os.getenv("API_KEY")
llm = ChatGoogleGenerativeAI(api_key=API_KEY, model="gemini-2.0-flash",temperature=0.1)
EMBEDDING_MODEL = "models/embedding-001"

embedding_function = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004", 
    google_api_key=API_KEY
)
