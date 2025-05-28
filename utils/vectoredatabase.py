from langchain_community.vectorstores import FAISS
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from utils.model import EMBEDDING_MODEL,API_KEY
import os

FAISS_INDEX_PATH = "faiss_index"

class FaissVectorStoreLoader:
    def __init__(self, embedding_model : str=EMBEDDING_MODEL, api_key : str = API_KEY, index_path:str=FAISS_INDEX_PATH):
        self.embedding = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key
        )
        self.index_path = index_path
        self.vector_store = None
        self.retriever = None

    def load_or_create(self, documents, index_name="default", overwrite=True):
        index_dir = os.path.join(self.index_path, index_name)
        index_file_path = os.path.join(index_dir, "index.faiss")

        index_exists = os.path.exists(index_file_path)

        if index_exists and not overwrite:
            print(f"[INFO] Loading existing FAISS index '{index_name}'...")
            self.vector_store = FAISS.load_local(index_dir, self.embedding, allow_dangerous_deserialization=True)
        else:
            if index_exists and overwrite:
                print(f"[INFO] Overwriting existing FAISS index '{index_name}'...")
            else:
                print(f"[INFO] Creating new FAISS index '{index_name}'...")

            os.makedirs(index_dir, exist_ok=True)
            self.vector_store = FAISS.from_documents(documents, self.embedding)
            self.vector_store.save_local(index_dir)

        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        return self.retriever


    def embedding_document(self, documents):
        self.vector_store = FAISS.from_documents(documents, self.embedding)
        self.retriever = self.vector_store.as_retriever()
        return self.retriever