import chromadb
from langchain_huggingface import HuggingFaceEmbeddings


# --- ChromaDB Setup ---
# Gunakan PersistentClient dan tentukan path untuk menyimpan database
client = chromadb.PersistentClient(path="./chroma_db") # <-- Perbaikan di sini

# Sisa kode tetap sama
collection = client.get_or_create_collection("cs_ai_knowledge")

# --- Embedding Model ---
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


