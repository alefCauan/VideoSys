import os
import uuid
import json
import sqlite3
import datetime
import cv2
from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for

# Config
MEDIA_ROOT = "media"
INCOMING = os.path.join(MEDIA_ROOT, "incoming")
VIDEOS = os.path.join(MEDIA_ROOT, "videos")
DB_PATH = "videos.db"

os.makedirs(INCOMING, exist_ok=True)
os.makedirs(VIDEOS, exist_ok=True)

app = Flask(__name__)

# --- Banco de Dados ---
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

init_db()

# --- Funções Auxiliares ---
def process_video(path_in, path_out, filter_type="gray"):
    cap = cv2.VideoCapture(path_in)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out = cv2.VideoWriter(path_out, fourcc, fps, (w, h), isColor=(filter_type != "gray"))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if filter_type == "gray":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif filter_type == "edges":
            frame = cv2.Canny(frame, 100, 200)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif filter_type == "pixel":
            frame = cv2.resize(frame, (64, 64), interpolation=cv2.INTER_LINEAR)
            frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_NEAREST)
        out.write(frame)

    cap.release()
    out.release()

def generate_thumbnail(video_path, thumb_path):
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (160, 90))
        cv2.imwrite(thumb_path, frame)
    cap.release()

# --- Rotas ---
@app.route("/", methods=["GET"])
def index():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, filename, filter, created_at FROM videos ORDER BY created_at DESC")
        rows = cur.fetchall()

    template = """
    <h1>Vídeos Processados</h1>
    <form action="{{ url_for('upload') }}" method="post" enctype="multipart/form-data">
        <input type="file" name="video">
        <select name="filter">
            <option value="gray">Escala de Cinza</option>
            <option value="edges">Detecção de Bordas</option>
            <option value="pixel">Pixelização</option>
        </select>
        <button type="submit">Upload</button>
    </form>
    <hr>
    {% for id, filename, filter, created_at in rows %}
        <div>
            <p><b>{{ id }}</b> ({{ filter }}) - {{ created_at }}</p>
            <a href="{{ url_for('serve_video', video_id=id) }}">
                <img src="{{ url_for('serve_thumb', video_id=id) }}" />
            </a>
        </div>
    {% endfor %}
    """
    return render_template_string(template, rows=rows)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["video"]
    filter_type = request.form.get("filter", "gray")
    if not file:
        return "Nenhum arquivo enviado", 400

    tmp_path = os.path.join(INCOMING, file.filename)
    file.save(tmp_path)

    vid_uuid = str(uuid.uuid4())
    today = datetime.date.today()
    out_dir = os.path.join(VIDEOS, today.strftime("%Y"), today.strftime("%m"), today.strftime("%d"), vid_uuid)
    os.makedirs(out_dir, exist_ok=True)

    out_video = os.path.join(out_dir, "video.mp4")
    process_video(tmp_path, out_video, filter_type)

    thumb_path = os.path.join(out_dir, "thumbs")
    os.makedirs(thumb_path, exist_ok=True)
    thumb_file = os.path.join(thumb_path, "thumb.jpg")
    generate_thumbnail(out_video, thumb_file)

    meta = {
        "uuid": vid_uuid,
        "filename": "video.mp4",
        "filter": filter_type,
        "created_at": today.isoformat()
    }
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO videos (id, filename, filter, created_at) VALUES (?, ?, ?, ?)",
                    (vid_uuid, "video.mp4", filter_type, today.isoformat()))
        conn.commit()

    os.remove(tmp_path)
    return redirect(url_for("index"))

@app.route("/videos/<video_id>")
def serve_video(video_id):
    # Procura vídeo
    for root, dirs, files in os.walk(VIDEOS):
        if video_id in root and "video.mp4" in files:
            return send_from_directory(root, "video.mp4")
    return "Vídeo não encontrado", 404

@app.route("/thumbs/<video_id>")
def serve_thumb(video_id):
    for root, dirs, files in os.walk(VIDEOS):
        if video_id in root and "thumbs" in dirs:
            return send_from_directory(os.path.join(root, "thumbs"), "thumb.jpg")
    return "Thumb não encontrada", 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
