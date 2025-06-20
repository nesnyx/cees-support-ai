from config.db import db

class ProductService:
    def __init__(self,name="", price="", category=""):
        self.name = name
        self.price = price
        self.category = category
        self.db = db
        self.user_id = user_id
    def create(self):
        try:
            product = self.db.product.post(self.name, self.price, self.category)
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
            product = self.db.product.get_all()
            return {
                "status":True,
                "data":product
            }
        except Exception as e:
            print(f"Database query error: {e}")
            return {
                "status":False,
            }

    def get_by_id(self, id):
        try:
            product = self.db.product.get_by_id(id)
        except Exception as e:
            print(f"Database query error: {e}")
            return {
                "status":False,
            }


    def delete(self, id):
        try:
            product = self.db.product.delete(id)
            if product == False:
                return {
                    "status":False,
                } 
            return {
                "status":True,
            }
        except Exception as e:
            print(f"Database query error: {e}")
            return {
                "status":False,
            }   
            