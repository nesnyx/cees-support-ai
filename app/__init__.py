from fastapi import FastAPI
from app.router.chatbot import router_chat
from app.router.products import router_product
from app.router.prompts import router_prompts
from app.router.authentication import authentication_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Customer Service AI",root_path="/api/v1")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.include_router(router=router_product)
app.include_router(router=router_prompts)
app.include_router(router=router_chat)
app.include_router(router=authentication_router)


origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, 
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


