from pydantic import BaseModel
from typing import Optional

class ProductInput(BaseModel):
    name : str
    price : int
    description : str


class ProductID(BaseModel):
    id : str


class ProductModel(BaseModel):
    id : Optional[str]
    name : str
    user_id : str
    description : str
    price : int

class ProductUpdate(BaseModel):
    name : str
    price : int
    description : str