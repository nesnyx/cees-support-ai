from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id : int
    username: str

# Model ini bisa diperluas dengan field lain seperti email, full_name, dll.