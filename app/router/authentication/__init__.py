
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter,Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.service.authentication import create_access_token,get_current_user,verify_password,get_password_hash
from app.service.authentication.models import User, Token
from app.router.authentication.model import RegisterInput
from app.service.authentication import AccountService,verify_cookie
from app.service.database.auth import Auth
from utils.security import encrypt_cookie,decrypt_cookie
from config.mysql import get_db
authentication_router = APIRouter(prefix="/authentication")

@authentication_router.post("/login")
async def login_for_access_token(response : Response,request : Request, form_data : OAuth2PasswordRequestForm = Depends(),db: AsyncSession = Depends(get_db)):
    # token = request.cookies.get("session_user")
    # if token:
    #     raise HTTPException(
    #         status_code=409,
    #         detail="Akun sudah login",
    #     )
    user = Auth(form_data.username, form_data.password,db)
    check_login= await user.login()
    if check_login['status'] == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=check_login['detail'],
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"username": check_login["data"]["username"],"id":check_login["data"]["id"]}
    )
    # encrypt_token = encrypt_cookie(access_token)
    # response.set_cookie(
    #     key="session_user",
    #     value=access_token,
    #     httponly=True,       # Tidak bisa diakses JavaScript (mencegah XSS)
    #     secure=True,         # Hanya dikirim via HTTPS (jangan lupa pakai HTTPS di production)
    #     samesite="strict",   # Mencegah CSRF
    #     max_age=60*60*24,    # Expired 1 hari
    #     path="/"
    # )
    
    return {"access_token": access_token ,"token_type": "bearer"}



@authentication_router.get("/users/me")
async def read_cookies(request : Request,current_user = Depends(get_current_user)):
    return {"user_id": current_user['id'],"username":current_user["username"]}
    

@authentication_router.post("/register")
async def register(input_account : RegisterInput,db: AsyncSession = Depends(get_db)):
    try:
        user = Auth(input_account.username, input_account.password,db=db)
        register_account = await user.register()
        if register_account['status'] == False:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="failed to register")
        return JSONResponse(status_code=status.HTTP_201_CREATED,content={
            "code":status.HTTP_201_CREATED,
            "detail":register_account
        })
    except Exception as e:
        print(f"Error : {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Something Error")



# TESTING
