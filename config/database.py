from langchain_core.documents import Document
import sqlite3
import time

DATABASE_PATH = "sablon.db"

class ProductHandler:
    def __init__(self,db:str):
        self.db = db
    def get(self):
        try:
            with sqlite3.connect(self.db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products")
                rows = cursor.fetchall()
                documents = []
                for row in rows:
                    name = row[1]
                    category = row[2]
                    price = row[3]
                    content = f"name: {name}, price: {price}"
                    metadata = {"name": name, "price": price}
                    documents.append(Document(page_content=content, metadata=metadata))
                return documents
        except sqlite3.Error as e:
            print(f"Database query error: {e}")
            return []

    def post(self,name,price,category):
        timestamp = int(time.time())
        try:
            with sqlite3.connect(self.db) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO products (name, category,price,createdAt) VALUES (?, ?, ?, ?)",(name,category,price,timestamp))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database query error: {e}")
            return False

    def get_all(self):
        try:
            with sqlite3.connect(self.db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products")
                rows = cursor.fetchall()
                return rows
        except sqlite3.Error as e:
            print(f"Database query error: {e}")
            return []


class SablonInfoHandler:
    def __init__(self,db:str):
        self.db = db
    def get(self):
        try:
            with sqlite3.connect(self.db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sablon_info")
                rows = cursor.fetchall()
                documents = []
                for row in rows:
                    kategori = row[1]
                    keyword = row[2]
                    isi = row[3]
                    content = f"kategori: {kategori}, keyword: {keyword}, isi: {isi}"
                    metadata = {"kategori": kategori, "keyword": keyword, "isi": isi}
                    documents.append(Document(page_content=content, metadata=metadata))
                return documents
        except sqlite3.Error as e:
            print(f"Database query error: {e}")
            return []


class Database:
    def __init__(self,path : str):
        self.path = path
        self.product = ProductHandler(self.path)
        self.sablon_info = SablonInfoHandler(self.path)


db = Database(DATABASE_PATH)
