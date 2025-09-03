# storage/manager.py
import os
import json
import hashlib
import sqlite3
import datetime
import cv2
import mimetypes


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DB_PATH = os.path.join(BASE_DIR, "database", "videos.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                original_name TEXT,
                original_ext TEXT,
                mime_type TEXT,
                size_bytes INTEGER,
                duration_sec REAL,
                fps REAL,
                width INTEGER,
                height INTEGER,
                filter TEXT,
                created_at TEXT,
                path_original TEXT,
                path_processed TEXT
            )
        """)
        conn.commit()

def compute_checksum(file_path):
    """Calcula o checksum MD5 de um arquivo."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def extract_video_info(video_path):
    """Extrai informações básicas de um vídeo com OpenCV."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration_sec = frame_count / fps if fps > 0 else 0
    cap.release()
    return fps, width, height, duration_sec

def save_meta_json(video_id, original_name, filter_type, video_path, thumb_path, output_dir):
    """Gera e salva o meta.json na pasta do vídeo e retorna dict completo para o BD."""
    fps, width, height, duration_sec = extract_video_info(video_path)
    checksum = compute_checksum(video_path)

    # --- JSON leve (apenas alguns campos) ---
    meta = {
        "uuid": video_id,
        "original_name": original_name,
        "original_ext": os.path.splitext(original_name)[1].lstrip("."),
        "filter": filter_type,
        "checksum": checksum,
        "created_at": datetime.datetime.now().isoformat(),
        "fps": fps,
        "width": width,
        "height": height,
        "duration_sec": duration_sec,
        "path_original": video_path,
        "path_thumb": thumb_path
    }

    meta_path = os.path.join(output_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # --- Dados completos para o banco ---
    mime_type, _ = mimetypes.guess_type(original_name)
    if mime_type is None:
        mime_type = "application/octet-stream"

    size_bytes = os.path.getsize(video_path)

    db_record = {
        "id": video_id,
        "original_name": original_name,
        "original_ext": os.path.splitext(original_name)[1].lstrip("."),
        "mime_type": mime_type,
        "size_bytes": size_bytes,
        "duration_sec": duration_sec,
        "fps": fps,
        "width": width,
        "height": height,
        "filter": filter_type,
        "created_at": meta["created_at"],
        "path_original": video_path,
        "path_processed": f"{filter_type}_{os.path.basename(video_path)}"  
    }

    print(db_record)  # Debug print

    return db_record
