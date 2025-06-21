from fastapi import APIRouter,status,Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from app.router.products.model import ProductInput, ProductID, ProductModel, ProductUpdate
from app.service.products import ProductService
from app.service.database.products import insert_product,get_product_by_id,update_product,delete_product
from app.router.authentication import verify_cookie,get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from config.mysql import get_db
from app.service.chromadb import upsert_product_to_chroma,delete_product_from_chroma,check_product_exists
from app.service.database.products import get_all_products_by_user
import logging

router_product = APIRouter(prefix="/products")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@router_product.get("/chroma/get-by-id")
async def get_chroma_product(input : ProductID):
    check_product = check_product_exists(input.id)
    return check_product


@router_product.post("/create")
async def create(request : Request,input : ProductInput ,db: AsyncSession = Depends(get_db),current_user = Depends(get_current_user)):
    try:   
        product = await insert_product(db,input,current_user["id"])
        if product["status"] == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Gagal membuat produk: {product.get('error', 'Unknown error')}"
            )
        new_id = product["id"]
        newly_created_product = await get_product_by_id(db,new_id,current_user["id"])
        if newly_created_product:
            upsert_product_to_chroma(newly_created_product)

        return { "code":status.HTTP_201_CREATED,
            "detail":newly_created_product}
    except Exception as e:
        logging.info(f"Error Message : {e} ")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Error")



@router_product.put("/update/{product_id}")
async def update(product_id: str, 
    product_update: ProductUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user)):
    existing_product = None
    user_id = current_user["id"]
    product = await update_product(db,product_id,user_id,product_data=product_update)
    if not product:
        existing_product = await get_product_by_id(db, product_id, user_id)
        if not existing_product:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan atau Anda tidak punya hak akses.")
        raise HTTPException(status_code=500, detail="Gagal memperbarui produk.")
    get_product_updated = await get_product_by_id(db, product_id, user_id)
    print(f"Update Product : {get_product_updated}")
    print(f"Update Product existing : {existing_product}")
    if get_product_updated:
        upsert_product_to_chroma(get_product_updated)
    
    return {
            "code":status.HTTP_200_OK,
            "detail":get_product_updated
    }
    


@router_product.delete("/delete/{product_id}")
async def delete_product_endpoint(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user_id = current_user["id"]
    delete_product_success = await delete_product(db, product_id, user_id)
    print(f"delete : {delete_product_success}")
    if not delete_product_success:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan atau Anda tidak punya hak akses.")
    delete_product_from_chroma(product_id)

    return {"status":"true"}

@router_product.get("/users")
async def read_users_me(request : Request,db: AsyncSession = Depends(get_db),current_user = Depends(get_current_user)):
    products = await get_all_products_by_user(db,current_user['id'])
    return {
        "data":products
    }