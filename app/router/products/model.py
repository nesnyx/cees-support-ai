from pydantic import BaseModel

class ProductInput(BaseModel):
    name : str
    price : int
    category : str