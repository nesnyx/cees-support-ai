from langchain_chroma import Chroma
from utils.model import embedding_function
from utils.chromadb import collection,client,embedding_model
from langchain_core.documents import Document

vectorstore = Chroma(
    client=client,
    collection_name="cs_ai_knowledge",
    embedding_function=embedding_model
)


def check_product_exists(product_id: str) -> bool:
    chroma_id = f"product_{product_id}"
    results = collection.get(ids=[chroma_id])
    return len(results['ids']) > 0


def _create_product_document(product) -> str:
    description = product['description'] if product['description'] else "Tidak ada deskripsi."
    return (f"Nama Produk: {product['name']}\n"f"Deskripsi: {description}\n" f"Harga: {product['price']}")


def upsert_product_to_chroma(product):
    document = _create_product_document(product)
    chroma_id = f"product_{product['id']}"
    collection.upsert(
        ids=[chroma_id],
        documents=[document],
        metadatas=[{"user_id": product['user_id'], "product_id": product['id']}]
    )
    print(f"Product {product['id']} berhasil di-upsert ke ChromaDB.")



def delete_product_from_chroma(product_id: str):
    """Menghapus vektor produk dari ChromaDB."""
    chroma_id = f"product_{product_id}"
    collection.delete(ids=[chroma_id])
    print(f"Product vector {product_id} deleted from ChromaDB.")