from langchain_core.documents import Document
import sqlite3
import time

# AKAN ADA PERUBAHAAN MENYESUAIKAN USER
DATABASE_PATH = "database/sablon.db"

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

    def get_by_id(self, id):
        try:
            with sqlite3.connect(self.db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM products WHERE id = ?",id)
                rows = cursor.fetchone()
                print(rows)
                return rows
        except sqlite3.Error as e:
            print(f"Database query error: {e}")
            return []
            
    def delete(self, id : int):
        try:
            with sqlite3.connect(self.db) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id = ?", (id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database query error: {e}")
            return False


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


class AccountHandler:
    def __init__(self,db:str):
        self.db = db
    
    def register(self, username,password,hash):
        timestamp = int(time.time())
        try:
            with sqlite3.connect(self.db) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO account (username, password, hash, createdAt) VALUES (?, ?, ?, ?)",(username,password,hash,timestamp))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database query error: {e}")
            return False

    def get_by_username(self,username):
        try:
            with sqlite3.connect(self.db) as conn:
               
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM account WHERE username = ?",(username,))
                rows = cursor.fetchone()
                return rows
        except sqlite3.Error as e:
            print(f"Database query error: {e}")
            return []

class Database:
    def __init__(self,path : str):
        self.path = path
        self.product = ProductHandler(self.path)
        self.sablon_info = SablonInfoHandler(self.path)
        self.account = AccountHandler(self.path)


db = Database(DATABASE_PATH)
