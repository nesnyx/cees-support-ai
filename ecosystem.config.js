// ecosystem.config.js
module.exports = {
  apps : [
    {
      name   : "cees-ai",
      script : "uvicorn",
      args   : "app:app --host 127.0.0.1 --port 3005",
    //   interpreter: "/path/to/your/env/bin/activate", // Ganti dengan path ke python di venv Anda
      cwd    : "/home/bara/big-project/cees-ai", // Ganti dengan path ke root proyek Anda
      watch  : false, // Set true hanya jika ingin auto-restart saat file berubah (tidak disarankan di prod)
      autorestart: true,
    },
    {
      name   : "celery-worker",
      script : "celery",
      args   : "-A celery_worker.celery_app worker --loglevel=info",
    //   interpreter: "/path/to/your/env/bin/activate", // Ganti dengan path yang sama
      cwd    : "/home/bara/big-project/cees-ai", // Ganti dengan path yang sama
      watch  : false,
      autorestart: true,
    },
    {
      // REKOMENDASI TAMBAHAN: Gunakan Flower untuk memantau Celery via web UI
      name   : "celery-flower",
      script : "celery",
      args   : "-A celery_worker.celery_app flower --port=5555",
    //   interpreter: "/path/to/your/env/bin/activate", // Ganti dengan path yang sama
      cwd    : "/home/bara/big-project/cees-ai", // Ganti dengan path yang sama
      watch  : false,
      autorestart: true,
    }
  ]
}