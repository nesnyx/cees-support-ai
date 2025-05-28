from config.database import db

class ProductService:
    def __init__(self,name="", price="", category=""):
        self.name = name
        self.price = price
        self.category = category
        self.db = db
    def create(self):
        try:
            product = db.product.post(self.name, self.price, self.category)
            return {
                "status":True,
                "data":product
            }
        except Exception as e:
            print(f"Database query error: {e}")
            return {
                "status":False,
            }
    
    def get(self):
        try:
            product = db.product.get_all()
            return {
                "status":True,
                "data":product
            }
        except Exception as e:
            print(f"Database query error: {e}")
            return {
                "status":False,
            }


            