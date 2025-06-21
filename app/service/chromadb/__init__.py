import traceback
from langchain_chroma import Chroma
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from utils.model import embedding_function

client = chromadb.PersistentClient(path="./chroma_db") # <-- Perbaikan di sini
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection("cs_ai_knowledge")
vectorstore = Chroma(
    client=client,
    collection_name="cs_ai_knowledge",
    embedding_function=embedding_model
)
def check_product_exists(product_id: str) -> bool:
    chroma_id = f"product_{product_id}"
    results = collection.get(ids=[chroma_id])
    return len(results['ids']) > 0



_client = None
_embedding_model = None
_collection = None


def get_collection():
    """
    Fungsi ini bertanggung jawab untuk menyediakan collection object yang valid.
    Ia akan membuat koneksi jika belum ada. Ini adalah kunci solusinya.
    """
    global _client, _embedding_model, _collection

    # Hanya inisialisasi jika belum pernah dibuat di dalam proses ini
    if _collection is None:
        print("[INIT] Objek collection belum ada, memulai inisialisasi...")
        try:
            # 1. Inisialisasi Embedding Model
            print("[INIT] Membuat embedding model 'all-MiniLM-L6-v2'...")
            _embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            print("[INIT] Embedding model SUKSES dibuat.")

            # 2. Inisialisasi ChromaDB Client
            print("[INIT] Menghubungkan ke PersistentClient di path './chroma_db'...")
            _client = chromadb.PersistentClient(path="./chroma_db")
            print("[INIT] ChromaDB Client SUKSES terhubung.")

            # 3. Mendapatkan Collection
            print("[INIT] Mendapatkan/membuat collection 'products'...")
            _collection = _client.get_or_create_collection(
                name="cs_ai_knowledge", 
                embedding_function=_embedding_model
            )
            print("[INIT] Collection 'products' SUKSES didapatkan.")
        except Exception as e:
            print(f"[INIT_FATAL_ERROR] Gagal total saat inisialisasi ChromaDB: {e}")
            traceback.print_exc()
            raise  # Hentikan proses jika inisialisasi gagal

    return _collection


def _create_product_document(product: dict) -> str:
    description = product.get('description') or "Tidak ada deskripsi."
    return (
        f"Nama Produk: {product.get('name')}\n"
        f"Deskripsi: {description}\n"
        f"Harga: {product.get('price')}"
    )


def upsert_product_to_chroma(product: dict):
    print(f"\n[UPSERT] Memulai proses untuk product ID: {product.get('id')}")
    try:
        # Panggil fungsi helper untuk mendapatkan collection yang valid
        collection = get_collection()

        document = _create_product_document(product)
        chroma_id = f"product_{product.get('id')}"

        print(f"[UPSERT] Melakukan upsert untuk ID '{chroma_id}'...")
        collection.upsert(
            ids=[chroma_id],
            documents=[document],
            metadatas=[{"user_id": str(product.get('user_id')), "product_id": str(product.get('id'))}]
        )
        print(f"[UPSERT] SUKSES untuk ID '{chroma_id}'.")

    except Exception as e:
        print(f"\n[UPSERT_FATAL_ERROR] Gagal saat upsert: {e}")
        traceback.print_exc()


def delete_product_from_chroma(product_id: str):
    print(f"\n[DELETE] Memulai penghapusan untuk product ID: {product_id}")
    try:
        collection = get_collection()
        chroma_id = f"product_{product_id}"
        
        print(f"[DELETE] Melakukan delete untuk ID '{chroma_id}'...")
        collection.delete(ids=[chroma_id])
        print(f"[DELETE] SUKSES untuk ID '{chroma_id}'.")

    except Exception as e:
        print(f"\n[DELETE_FATAL_ERROR] Gagal saat delete: {e}")
        traceback.print_exc()