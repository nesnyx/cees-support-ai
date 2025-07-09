from config.postgresql import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from app.router.products.model import ProductModel, ProductInput, ProductUpdate
import uuid

class Product:
    def __init__(self,user_id : str, product_id : str,name:str ,db : AsyncSession):
        self.user_id = user_id
        self.product_id = product_id
        self.name = name
        self.db = db


    async def get_product(self):
        query = text("SELECT id, user_id, name, price, description FROM products WHERE user_id = :user_id")
        check_account =  await self.db.execute(query, {
            "user_id" : self.user_id
        })
        row = check_account.fetchone()
        if not row:
            return {"data" : {},"status":False}
        return {"data" : row,"status":True}

    

async def get_all_products_by_user(db: AsyncSession, user_id: int) -> list[dict]:
    """
    Mengambil semua produk milik satu user menggunakan raw SQL query.
    Mengembalikan list of dictionaries.
    """
    # Pastikan nama kolom (id, user_id, dst.) SAMA PERSIS dengan yang ada di tabel MySQL Anda.
    query = text("SELECT id, user_id, name, description, price FROM products WHERE user_id = :user_id")
    
    # Jalankan query dengan parameter yang aman
    result = await db.execute(query, {"user_id": user_id})
    
    # .mappings().all() mengubah setiap baris hasil menjadi objek mirip dictionary
    return result.mappings().all()


async def get_product_by_id(db: AsyncSession, product_id: str, user_id: str) -> dict | None:
    """
    Mengambil satu produk menggunakan raw SQL query, memastikan kepemilikan.
    Mengembalikan satu dictionary atau None jika tidak ditemukan.
    """
    query = text("""
        SELECT id, user_id, name, description, price 
        FROM products 
        WHERE id = :id AND user_id = :user_id
    """)
    
    result = await db.execute(query, {"id": product_id, "user_id": user_id})
    row = result.mappings().first()
    print(f"Get product by id : {row}")
    if not row:
        return None
    
    return row
    



async def insert_product(db: AsyncSession,name,price,description, image,user_id: str):
        new_product_id = str(uuid.uuid4())
        query = text("INSERT INTO products(id,user_id, name, price,image_url, description) VALUES (:id,:user_id, :name, :price,:image_url, :description )")
        try:
            await db.execute(query, {
                "id": new_product_id,
                "user_id": user_id,
                "name": name,
                "price": price,
                "image_url": image,
                "description": description
            })
            await db.commit()
            return {"status": True, "id": new_product_id}
        except Exception as e:
            print(f"Error database : {e}")
            await db.rollback()
            return {"status": False, "id": None, "error": str(e)}



async def update_product(db: AsyncSession, product_id: str, user_id: str, product_data: ProductUpdate) -> bool:
    """
    Memperbarui data produk di database MySQL menggunakan raw query.
    """
    query = text("""
        UPDATE products
        SET name = :name, description = :description, price = :price
        WHERE id = :product_id AND user_id = :user_id
    """)
    try:
        result = await db.execute(query, {
            "name": product_data.name,
            "description": product_data.description,
            "price": product_data.price,
            "product_id": product_id,
            "user_id": user_id
        })
        if result.rowcount == 0:
            return False 
        
        await db.commit()
        return True
    except Exception:
        await db.rollback()
        return False


async def delete_product(db: AsyncSession, product_id: str, user_id: str) -> bool:
    """
    Menghapus data produk dari database MySQL.
    """
    query = text("DELETE FROM products WHERE id = :product_id AND user_id = :user_id")
    try:
        result = await db.execute(query, {"product_id": product_id, "user_id": user_id})
        if result.rowcount == 0:
            return False
        await db.commit()
        return True
    except Exception as e:
        print(f"Error database : {e}")
        await db.rollback()
        return False