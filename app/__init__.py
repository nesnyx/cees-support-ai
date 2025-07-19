from contextlib import asynccontextmanager
import time
import logging, os, shutil, asyncio
from fastapi import FastAPI, APIRouter
from app.router.chatbot import router_chat
from app.router.products import router_product
from app.router.prompts import router_prompts
from app.router.authentication import authentication_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# async def periodic_task():
#     while True:
#         try:
#             print("🕒 Menjalankan tugas periodik...")
#             await asyncio.sleep(10)
#         except asyncio.CancelledError:
#             print("Tugas periodik dibatalkan.")
#             break
#         except Exception as e:
#             print(f"Terjadi error pada tugas periodik: {e}")
#             await asyncio.sleep(10) 



# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("🚀 Aplikasi mulai berjalan. Menjadwalkan tugas periodik...")
#     background_task = asyncio.create_task(periodic_task())
#     yield 
#     print("Aplikasi berhenti. Menghentikan tugas background...")
#     background_task.cancel()
#     try:
#         await background_task
#     except asyncio.CancelledError:
#         print("Tugas background berhasil dihentikan.")


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Customer Service AI")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="public"), name="static")
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(router_product)
api_router.include_router(router_prompts)
api_router.include_router(router_chat)
api_router.include_router(authentication_router)

app.include_router(api_router)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
