from fastapi import APIRouter,status,Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from app.router.products.model import ProductInput, ProductID, ProductModel, ProductUpdate
from app.service.products import ProductService
from app.service.database.products import insert_product,get_product_by_id,update_product,delete_product

from app.router.authentication import verify_cookie,get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from config.mysql import get_db
from app.service.chromadb import check_product_exists
from app.tasks import sync_product_to_vector_db, delete_product_from_vector_db
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
        sync_product_to_vector_db.delay(product['id'], current_user['id'])
        
        return { "code":status.HTTP_201_CREATED,
            "msg":'success to created product'}
    except Exception as e:
        await db.rollback()
        logging.info(f"Error Message : {e} ")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Error")



@router_product.put("/update/{product_id}")
async def update(product_id: str, 
    product_update: ProductUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user)):
    try:
        user_id = current_user["id"]
        update_product = await update_product(db,product_id,user_id,product_data=product_update)
        if not updated_product:
                raise HTTPException(status_code=404, detail="Product not found")
        sync_product_to_vector_db.delay(product_id=product_id,user_id=user_id)
        return {"status": "success", "message": "Product updated and sync scheduled."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    


@router_product.delete("/delete/{product_id}")
async def delete(product_id: str, current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        deleted = await  delete_product(db,product_id,current_user['id'])
        if not deleted:
            raise HTTPException(status_code=404, detail="Product not found")

        delete_product_from_vector_db.delay(product_id=str(product_id))
        
        return {"status": "success", "message": "Product deleted and removal scheduled."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router_product.get("/users")
async def read_users_me(request : Request,db: AsyncSession = Depends(get_db),current_user = Depends(get_current_user)):
    products = await get_all_products_by_user(db,current_user['id'])
    return {
        "data":products
    }