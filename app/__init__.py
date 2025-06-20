from fastapi import FastAPI
# from app.router.chatbot import router_chat
from app.router.chatbot import router_chat
from app.router.products import router_product
from app.router.prompts import router_prompts
from app.router.authentication import authentication_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Customer Service AI",root_path="/api/v1")

app.include_router(router=router_product)
app.include_router(router=router_prompts)
app.include_router(router=router_chat)
# app.include_router(router=router_chat)

# Authentication
app.include_router(router=authentication_router)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # INI YANG PALING PENTING untuk cookie
    allow_methods=["*"],
    allow_headers=["*"],
)
# https://arisbara.cloud/api/v1/products/create
# https://arisbara.cloud/api/v1/products/get-all
# https://arisbara.cloud/api/v1/prompts//create


