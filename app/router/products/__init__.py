import time
from fastapi import (
    APIRouter,
    status,
    Request,
    Depends,
    Form,
    File,
    UploadFile,
    BackgroundTasks,
    FastAPI,
)
from contextlib import asynccontextmanager
from fastapi.exceptions import HTTPException
from sqlalchemy import text
from app.router.products.model import ProductInput, ProductID, ProductUpdate
from app.service.database.products import (
    insert_product,
    get_product_by_id,
    update_product,
    delete_product,
)
from app.router.authentication import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from config.postgresql import get_db
from app.service.chromadb import (
    upsert_product_to_chroma,
    delete_product_from_chroma,
    check_product_exists,
)
from PIL import Image
import logging, os, shutil, asyncio



router_product = APIRouter(prefix="/products")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_ROOT = "public/uploads"
BASE_IMAGE_URL = "https://cees.arisbara.cloud/static"


@router_product.get("/chroma/get-by-id")
async def get_chroma_product(input: ProductID):
    check_product = check_product_exists(input.id)
    return check_product


@router_product.post("/create")
async def create(
    request: Request,
    name: str = Form(...),
    price: int = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        # Buat folder untuk user jika belum ada
        user_id = current_user["id"]
        user_folder = os.path.join(UPLOAD_ROOT, user_id)
        os.makedirs(user_folder, exist_ok=True)

        # Cek ekstensi gambar
        file_ext = os.path.splitext(image.filename)[1].lower()
        if file_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(status_code=400, detail="Format gambar tidak didukung.")

        # Ubah nama file (misal berdasarkan nama produk)
        safe_name = name.replace(" ", "_")  # Hindari spasi
        filename = f"{safe_name}{file_ext}"
        file_path = os.path.join(user_folder, filename)

        # Simpan gambar ke disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Simpan path relatif ke database
        image_url = f"{user_id}/{filename}"  # disimpan sebagai path relatif

        # Insert ke database
        product = await insert_product(db, name, price, description, image_url, user_id)
        if not product["status"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Gagal membuat produk: {product.get('error', 'Unknown error')}",
            )

        new_id = product["id"]
        # Optional: ambil ulang produk untuk ditampilkan atau simpan ke search index
        newly_created_product = await get_product_by_id(db, new_id, user_id)

        return {
            "code": status.HTTP_201_CREATED,
            "detail": newly_created_product,
        }

    except Exception as e:
        logging.error(f"❌ Error saat membuat produk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Terjadi kesalahan saat membuat produk.",
        )


@router_product.put("/update/{product_id}")
async def update(
    product_id: str,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    existing_product = None
    user_id = current_user["id"]
    product = await update_product(db, product_id, user_id, product_data=product_update)
    if not product:
        existing_product = await get_product_by_id(db, product_id, user_id)
        if not existing_product:
            raise HTTPException(
                status_code=404,
                detail="Produk tidak ditemukan atau Anda tidak punya hak akses.",
            )
        raise HTTPException(status_code=500, detail="Gagal memperbarui produk.")
    get_product_updated = await get_product_by_id(db, product_id, user_id)
    print(f"Update Product : {get_product_updated}")
    print(f"Update Product existing : {existing_product}")
    if get_product_updated:
        upsert_product_to_chroma(get_product_updated)

    return {"code": status.HTTP_200_OK, "detail": get_product_updated}


@router_product.delete("/delete/{product_id}")
async def delete_product_endpoint(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user["id"]
    product = await get_product_by_id(db, product_id, user_id)
    print(product)
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Produk tidak ditemukan atau Anda tidak punya hak akses.",
        )

    image_url = product.get("image_url")
    if image_url:
        image_path = os.path.join(UPLOAD_ROOT, image_url)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                logger.info(f"🗑️ Gambar berhasil dihapus: {image_path}")
            except Exception as e:
                logger.error(f"❌ Gagal menghapus gambar: {e}")
        else:
            logger.warning(f"⚠️ Gambar tidak ditemukan di path: {image_path}")

    delete_product_success = await delete_product(db, product_id, user_id)
    print(f"delete : {delete_product_success}")
    if not delete_product_success:
        raise HTTPException(
            status_code=404,
            detail="Produk tidak ditemukan atau Anda tidak punya hak akses.",
        )
    delete_product_from_chroma(product_id)

    return {"status": "true"}


@router_product.get("/users")
async def get_user_products(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        user_id = current_user["id"]
        query = text(
            """
            SELECT id, name, price, description, image_url
            FROM products
            WHERE user_id = :user_id
        """
        )
        result = await db.execute(query, {"user_id": user_id})
        products = result.mappings().all()

        if not products:
            return {"code": 200, "data": [], "message": "Kamu belum punya produk."}

        # Tambahkan full image URL
        product_list = []
        for product in products:
            product_dict = dict(product)
            if product_dict["image_url"]:
                product_dict["image_url"] = (
                    f"{BASE_IMAGE_URL}/uploads/{product_dict['image_url']}"
                )
            product_list.append(product_dict)

        return {"code": 200, "data": product_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")






