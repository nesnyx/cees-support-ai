from fastapi import FastAPI
from app.router.chatbot import router_chatbot
from app.router.products import router_product
app = FastAPI(title="Customer Service AI",root_path="/api/v1")

app.include_router(router=router_chatbot)
app.include_router(router=router_product)


