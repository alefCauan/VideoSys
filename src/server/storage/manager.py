# Funções para salvar/recuperar vídeos# storage/manager.py
import os
import json
import sqlite3
import datetime
from pathlib import Path

DB_PATH = "videos.db"

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

def save_metadata(uuid, filter_type, out_dir):
    meta = {
        "uuid": uuid,
        "filename": "video.mp4",
        "filter": filter_type,
        "created_at": datetime.date.today().isoformat()
    }
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO videos (id, filename, filter, created_at) VALUES (?, ?, ?, ?)",
                    (uuid, "video.mp4", filter_type, meta["created_at"]))
        conn.commit()
