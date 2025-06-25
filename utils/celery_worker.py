from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# Inisialisasi aplikasi Celery
# 'app' adalah nama modul utama tempat task berada (kita akan buat app.tasks)
celery_app = Celery(
    'tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['app.tasks'] # <-- Beri tahu Celery di mana menemukan file tasks
)


# Konfigurasi opsional untuk meningkatkan keandalan
celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Asia/Jakarta', # Sesuaikan dengan timezone Anda
    enable_utc=True,
)

if __name__ == '__main__':
    celery_app.start()