from utils.celery_worker import celery_app
from app.service.chromadb import upsert_product_to_chroma, delete_product_from_chroma
from celery.exceptions import MaxRetriesExceededError
from app.service.database.products import get_product_by_id
from config.mysql import SyncSessionLocal
from sqlalchemy import text

@celery_app.task(name="tasks.sync_product_to_vector_db", bind=True, max_retries=3, default_retry_delay=60)
def sync_product_to_vector_db(self, product_id: str,user_id :str):
    """
    Task untuk membuat atau mengupdate produk di ChromaDB.
    Task akan mencoba ulang maksimal 3 kali jika gagal, dengan jeda 60 detik.
    """
    print(f"Starting task to sync product_id: {product_id}")
    
    db = SyncSessionLocal()
    try:
        result = db.execute(text("SELECT id, user_id, name, description, price  FROM products WHERE id = :id AND user_id = :user_id"), {"id": product_id,"user_id":user_id})
        product = result.mappings().all()
        print("get product : ",product)
        if not product:
            print(f"Product with id {product_id} not found. Task will not retry.")
            return
        upsert_product_to_chroma(product[0])
        print(f"Successfully synced product_id: {product_id} to ChromaDB")
        return f"Product {product_id} synced successfully."
    except Exception as exc:
        print(f"Error syncing product_id: {product_id}. Retrying... Error: {exc}")
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            print(f"CRITICAL: Failed to sync product {product_id} after multiple retries.")
            return f"Failed to sync product {product_id}." # Kembalikan string
    finally:

        db.close()

@celery_app.task(name="tasks.delete_product_from_vector_db", bind=True, max_retries=3, default_retry_delay=60)
def delete_product_from_vector_db(self, product_id: str):
    """
    Task untuk menghapus produk dari ChromaDB.
    """
    print(f"Starting task to delete product_id: {product_id}")
    try:
        delete_product_from_chroma(product_id)
        print(f"Successfully deleted product_id: {product_id} from ChromaDB")
    except Exception as exc:
        print(f"Error deleting product_id: {product_id}. Retrying... Error: {exc}")
        raise self.retry(exc=exc)