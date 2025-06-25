# Backend Customer Service AI dengan RAG

Ini adalah layanan backend untuk aplikasi Customer Service (CS) AI yang dibangun menggunakan FastAPI. Proyek ini mengimplementasikan arsitektur canggih **Retrieval-Augmented Generation (RAG)** untuk menciptakan chatbot Q&A yang cerdas, di mana basis pengetahuannya selalu sinkron secara *real-time* dengan data produk yang dinamis.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-#009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.3+-#37814A?style=for-the-badge&logo=celery)](https://docs.celeryq.dev/en/stable/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-#D71F00?style=for-the-badge&logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-%235B3A9A?style=for-the-badge)](https://www.trychroma.com/)

---

## Fitur Utama

-   **REST API Modern**: Dibangun di atas FastAPI untuk performa tinggi dan pengembangan yang cepat.
-   **Autentikasi Aman**: Menggunakan JWT (JSON Web Tokens) untuk mengamankan endpoint.
-   **Manajemen Produk (CRUD)**: Endpoint lengkap untuk membuat, membaca, memperbarui, dan menghapus data produk.
-   **Sinkronisasi Asinkron**: Perubahan pada data produk secara otomatis disinkronkan ke database vektor (ChromaDB) menggunakan **Celery** dan **Redis**, tanpa memblokir API utama.
-   **Chatbot Cerdas (RAG)**: Endpoint chatbot yang menggunakan pengetahuan dari ChromaDB untuk memberikan jawaban yang relevan dan akurat terkait produk.
-   **Pemisahan Konfigurasi**: Manajemen konfigurasi yang bersih menggunakan Pydantic dan file `.env`.

## Arsitektur & Teknologi

Proyek ini menggunakan arsitektur microservice di mana layanan web dan tugas latar belakang dipisahkan untuk skalabilitas dan ketahanan.

-   **Framework**: FastAPI
-   **Database Utama**: MySQL (diakses secara asinkron dengan `SQLAlchemy` dan `asyncmy`)
-   **Database Vektor**: ChromaDB (untuk menyimpan *embeddings* dari data produk)
-   **Task Queue**: Celery (untuk menangani tugas sinkronisasi di latar belakang)
-   **Message Broker**: Redis (untuk antrean tugas Celery)
-   **AI & Embeddings**: LangChain dengan model dari `langchain-huggingface` atau `langchain-google-genai`.
-   **Server**: Uvicorn
-   **Process Manager (Rekomendasi)**: PM2

## Instalasi & Setup

Ikuti langkah-langkah berikut untuk menjalankan proyek ini secara lokal.

### 1. Prasyarat
- Python 3.11+
- MySQL Server
- Redis Server

### 2. Klona Repositori
```bash
git clone [https://github.com/nesnyx/cees-support-ai.git](https://github.com/nesnyx/cees-support-ai.git)
cd cees-support-ai
```

### 3. Buat dan Aktifkan Virtual Environment
```bash
# Membuat environment
python -m venv env

# Mengaktifkan di Linux/macOS
source env/bin/activate

# Mengaktifkan di Windows
.\env\Scripts\activate
```

### 4. Instal Dependensi
```bash
pip install -r requirement.txt
```
*Catatan: Jika ada error terkait library, coba jalankan `pip install --upgrade ...` untuk paket yang bermasalah seperti yang telah kita diskusikan.*

### 5. Konfigurasi Environment
Buat file bernama `.env` di direktori root proyek. Salin konten di bawah ini dan sesuaikan dengan konfigurasi lokal Anda.

```env
# URL Database Utama Anda
DATABASE_URL="mysql+asyncmy://user:password@host:port/dbname"

# Konfigurasi JWT
SECRET_KEY="kunci_rahasia_yang_sangat_kuat_dan_panjang"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Konfigurasi Celery & Redis
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/1"

# API Key untuk LLM (jika menggunakan model via API)
# GOOGLE_API_KEY="AIza..."
```

## Menjalankan Aplikasi

Anda perlu menjalankan dua proses utama secara terpisah: server web FastAPI dan worker Celery.

### Untuk Development

1.  **Jalankan Server FastAPI:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
    API akan tersedia di `http://localhost:8000`. Dokumentasi interaktif Swagger UI tersedia di `http://localhost:8000/docs`.

2.  **Jalankan Worker Celery (di terminal terpisah):**
    ```bash
    celery -A celery_worker.celery_app worker --loglevel=info
    ```
    Worker ini akan mendengarkan tugas baru dari Redis untuk melakukan sinkronisasi data.

### Rekomendasi untuk Produksi (Menggunakan PM2)

Untuk produksi, sangat disarankan menggunakan process manager seperti PM2.

1.  Buat file `ecosystem.config.js`:
    ```javascript
    module.exports = {
      apps : [
        {
          name   : "fastapi-server",
          script : "uvicorn",
          args   : "main:app --host 0.0.0.0 --port 8000",
          interpreter: "/path/to/your/env/bin/python"
        },
        {
          name   : "celery-worker",
          script : "celery",
          args   : "-A celery_worker.celery_app worker --loglevel=info",
          interpreter: "/path/to/your/env/bin/python"
        }
      ]
    }
    ```
    *Ganti `/path/to/your/env/bin/python` dengan path absolut ke interpreter Python di virtual environment Anda.*

2.  Jalankan dengan PM2:
    ```bash
    pm2 start ecosystem.config.js
    ```

## Struktur Proyek

```
.
├── app/
│   ├── router/         # Mendefinisikan semua endpoint API
│   ├── service/        # Logika bisnis dan interaksi dengan layanan eksternal
│   └── __init__.py
├── config/             # Konfigurasi database dan aplikasi
├── prompts/            # Template prompt untuk LLM
├── utils/              # Fungsi-fungsi helper (keamanan, model, dll.)
├── celery_worker.py    # Definisi aplikasi Celery
├── main.py             # Titik masuk utama aplikasi FastAPI
├── requirement.txt     # Daftar dependensi Python
└── README.md           # Anda sedang membacanya
```

## Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).