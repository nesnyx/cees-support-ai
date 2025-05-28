from fastapi import APIRouter,status,Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from app.router.products.model import ProductInput
from app.service.products import ProductService
import logging

router_product = APIRouter(prefix="/products")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router_product.post("/create")
async def create(input : ProductInput, request : Request):
    try:   
        product_service = ProductService(input.name, input.price, input.category)
        product = product_service.create()
        return JSONResponse(status_code=status.HTTP_201_CREATED,content={
            "code":status.HTTP_201_CREATED,
            "detail":product
        })
    except Exception as e:
        logging.info(f"Error Message : {e} ")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Error")



@router_product.get("/get-all")
async def get_all(request : Request):
    try:
        product = ProductService()
        return JSONResponse(status_code=status.HTTP_201_CREATED,content={
            "code":status.HTTP_201_CREATED,
            "detail":product.get()
        })
    except Exception as e:
        logging.info(f"Error Message : {e} ")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Error")
