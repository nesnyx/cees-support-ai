from pydantic import BaseModel

class RegisterInput(BaseModel):
    username : str
    password : str


class LoginInput(BaseModel):
    username : str
    password : str