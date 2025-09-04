import os
import uuid
import datetime
import cv2
from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for, jsonify

# imports locais
from storage import manager, paths
from filters import grayscale, edges, pixelate

manager.init_db()

app = Flask(__name__)

def process_video(input_path, output_path, filter_type="gray"):
    video_capture = cv2.VideoCapture(input_path)
    video_codec = cv2.VideoWriter_fourcc(*"mp4v")
    video_fps = video_capture.get(cv2.CAP_PROP_FPS)
    frame_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    video_writer = cv2.VideoWriter(output_path, video_codec, video_fps, (frame_width, frame_height), isColor=True)

    while True:
        frame_read_success, frame = video_capture.read()
        if not frame_read_success:
            break

        if filter_type == "gray":
            frame = grayscale.apply(frame)
        elif filter_type == "edges":
            frame = edges.apply(frame)
        elif filter_type == "pixel":
            frame = pixelate.apply(frame)

        video_writer.write(frame)

    video_capture.release()
    video_writer.release()

def generate_thumbnail(video_path, thumbnail_path):
    video_capture = cv2.VideoCapture(video_path)
    frame_read_success, frame = video_capture.read()
    if frame_read_success:
        frame = cv2.resize(frame, (160, 90))
        cv2.imwrite(thumbnail_path, frame)
    video_capture.release()

# --- Rotas ---
@app.route("/", methods=["GET"])
def index():
    with manager.sqlite3.connect(manager.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, original_name, filter, created_at FROM videos ORDER BY created_at DESC")
        rows = cur.fetchall()

    template = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Server - Galeria</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 100%;
                height: 100%; /* ou min-height: 100% */
                overflow-y: auto;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            }
            
            h1 {
                text-align: center;
                color: #2c3e50;
                margin-bottom: 30px;
                font-size: 2.5em;
                font-weight: 300;
            }
            
            .stats-section {
                display: flex;
                justify-content: center;
                gap: 30px;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }
            
            .stat-card {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                min-width: 150px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            }
            
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
                display: block;
            }
            
            .stat-label {
                color: #666;
                font-size: 14px;
                margin-top: 5px;
            }
            
            .videos-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 25px;
                margin-top: 30px;
            }
            
            .video-card {
                background: white;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }
            
            .video-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
            }
            
            .video-thumbnail {
                width: 100%;
                height: 180px;
                object-fit: cover;
                transition: transform 0.3s ease;
            }
            
            .video-card:hover .video-thumbnail {
                transform: scale(1.05);
            }
            
            .video-info {
                padding: 20px;
            }
            
            .video-id {
                font-size: 14px;
                color: #666;
                margin-bottom: 8px;
                font-family: 'Courier New', monospace;
            }
            
            .video-name {
                font-size: 18px;
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 10px;
                word-break: break-word;
            }
            
            .filter-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                margin-bottom: 10px;
            }
            
            .filter-gray {
                background: #6c757d;
                color: white;
            }
            
            .filter-edges {
                background: #28a745;
                color: white;
            }
            
            .filter-pixel {
                background: #fd7e14;
                color: white;
            }
            
            .video-date {
                font-size: 14px;
                color: #888;
            }
            
            .no-videos {
                text-align: center;
                padding: 60px 20px;
                color: #666;
            }
            
            .no-videos h2 {
                margin-bottom: 10px;
                color: #999;
            }
            
            @media (max-width: 768px) {
                .stats-section {
                    gap: 15px;
                }
                
                .stat-card {
                    min-width: 120px;
                    padding: 15px;
                }
                
                .videos-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Galeria de Vídeos</h1>
            
            {% if rows %}
                <div class="stats-section">
                    <div class="stat-card">
                        <span class="stat-number">{{ rows|length }}</span>
                        <div class="stat-label">Total de Vídeos</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{{ rows|selectattr('2', 'equalto', 'gray')|list|length }}</span>
                        <div class="stat-label">Escala de Cinza</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{{ rows|selectattr('2', 'equalto', 'edges')|list|length }}</span>
                        <div class="stat-label">Detecção de Bordas</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{{ rows|selectattr('2', 'equalto', 'pixel')|list|length }}</span>
                        <div class="stat-label">Pixelizados</div>
                    </div>
                </div>
                
                <div class="videos-grid">
                    {% for id, original_name, filter, created_at in rows %}
                        <div class="video-card">
                            <a href="{{ url_for('serve_video', video_id=id) }}" style="text-decoration: none;">
                                <img src="{{ url_for('serve_thumb', video_id=id) }}" 
                                     alt="Thumbnail do vídeo {{ original_name }}"
                                     class="video-thumbnail"
                                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYwIiBoZWlnaHQ9IjkwIiB2aWV3Qm94PSIwIDAgMTYwIDkwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8cmVjdCB3aWR0aD0iMTYwIiBoZWlnaHQ9IjkwIiBmaWxsPSIjZjVmNWY1Ii8+Cjx0ZXh0IHg9IjgwIiB5PSI0NSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iIGZpbGw9IiM5OTkiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIj5TZW0gSW1hZ2VtPC90ZXh0Pgo8L3N2Zz4K'">
                            </a>
                            <div class="video-info">
                                <div class="video-id">ID: {{ id }}</div>
                                <div class="video-name">{{ original_name }}</div>
                                <span class="filter-badge filter-{{ filter }}">
                                    {% if filter == 'gray' %}
                                        🎨 Escala de Cinza
                                    {% elif filter == 'edges' %}
                                        🔍 Detecção de Bordas
                                    {% elif filter == 'pixel' %}
                                        🟫 Pixelização
                                    {% endif %}
                                </span>
                                <div class="video-date">{{ created_at }}</div>
                            </div>
                        </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="no-videos">
                    <h2>📂 Nenhum vídeo encontrado</h2>
                    <p>A galeria está vazia no momento.</p>
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(template, rows=rows)

@app.route("/upload", methods=["POST"])
def upload():
    uploaded_file = request.files["video"]
    selected_filter = request.form.get("filter", "gray")
    if not uploaded_file:
        return "Nenhum arquivo enviado", 400

    temp_file_path = os.path.join(paths.INCOMING, uploaded_file.filename)
    uploaded_file.save(temp_file_path)

    video_uuid = str(uuid.uuid4())
    today_date = datetime.date.today()
    output_directory = os.path.join(paths.VIDEOS, today_date.strftime("%Y"), today_date.strftime("%m"), today_date.strftime("%d"), video_uuid)
    os.makedirs(output_directory, exist_ok=True)

    output_video_path = os.path.join(output_directory, "video.mp4")
    process_video(temp_file_path, output_video_path, selected_filter)

    # thumbnail
    thumbnail_directory = os.path.join(output_directory, "thumbs")
    os.makedirs(thumbnail_directory, exist_ok=True)
    thumbnail_file_path = os.path.join(thumbnail_directory, "thumb.jpg")
    generate_thumbnail(output_video_path, thumbnail_file_path)

    result = manager.save_meta_json(
        video_uuid,
        uploaded_file.filename,
        selected_filter,
        output_video_path,
        thumbnail_file_path,
        output_directory
    )
    

    # agora salvar no SQLite
    with manager.sqlite3.connect(manager.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO videos (
                id, original_name, original_ext, mime_type, size_bytes,
                duration_sec, fps, width, height,
                filter, created_at,
                path_original, path_processed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["id"],
            result["original_name"],
            result["original_ext"],
            result["mime_type"],
            result["size_bytes"],
            result["duration_sec"],
            result["fps"],
            result["width"],
            result["height"],
            result["filter"],
            result["created_at"],
            result["path_original"],
            result["path_processed"]
        ))
        conn.commit()

    os.remove(temp_file_path)
    return jsonify({
        "id": video_uuid,
        "video_url": url_for("serve_video", video_id=video_uuid, _external=True),
        "thumb_url": url_for("serve_thumb", video_id=video_uuid, _external=True)
    })

@app.route("/videos/<video_id>")
def serve_video(video_id):
    for root_dir, sub_dirs, files in os.walk(paths.VIDEOS):
        if video_id in root_dir and "video.mp4" in files:
            return send_from_directory(root_dir, "video.mp4")
    return "Vídeo não encontrado", 404

@app.route("/thumbs/<video_id>")
def serve_thumb(video_id):
    for root_dir, sub_dirs, files in os.walk(paths.VIDEOS):
        if video_id in root_dir and "thumbs" in sub_dirs:
            return send_from_directory(os.path.join(root_dir, "thumbs"), "thumb.jpg")
    return "Thumb não encontrada", 404

# Rota para visualizar vídeo em uma página dedicada
@app.route("/video/<video_id>/view")
def view_video(video_id):
    with manager.sqlite3.connect(manager.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, original_name, filter, created_at FROM videos WHERE id = ?", (video_id,))
        video = cur.fetchone()
    
    if not video:
        return "Vídeo não encontrado", 404
    
    template = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ video[1] }} - Video Processor</title>
        <style>
            body {
                margin: 0;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a1a;
                color: white;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
            }
            .back-link {
                color: #667eea;
                text-decoration: none;
                margin-bottom: 20px;
                display: inline-block;
            }
            .video-player {
                width: 100%;
                max-width: 800px;
                margin: 0 auto 20px;
                display: block;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            }
            .video-info {
                text-align: center;
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 10px;
                backdrop-filter: blur(10px);
            }
            .video-title {
                font-size: 24px;
                margin-bottom: 10px;
            }
            .video-meta {
                color: #ccc;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="{{ url_for('index') }}" class="back-link">← Voltar para Home</a>
            
            <video class="video-player" controls>
                <source src="{{ url_for('serve_video', video_id=video[0]) }}" type="video/mp4">
                Seu navegador não suporta o elemento de vídeo.
            </video>
            
            <div class="video-info">
                <h1 class="video-title">{{ video[1] }}</h1>
                <div class="video-meta">
                    <p>Filtro: {{ video[2] | title }} | Data: {{ video[3] }}</p>
                    <p>ID: {{ video[0] }}</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(template, video=video)

# Rota para deletar vídeo
@app.route("/video/<video_id>/delete", methods=["POST"])
def delete_video(video_id):
    import shutil
    
    with manager.sqlite3.connect(manager.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM videos WHERE id = ?", (video_id,))
        if not cur.fetchone():
            return "Vídeo não encontrado", 404
        
        # Remove do banco
        cur.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()
    
    # Remove arquivos físicos
    for root_dir, sub_dirs, files in os.walk(paths.VIDEOS):
        if video_id in root_dir:
            shutil.rmtree(root_dir)
            break
    
    return redirect(url_for("index"))

# Rota para API JSON (útil para integrações)
@app.route("/api/videos")
def api_videos():
    with manager.sqlite3.connect(manager.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, original_name, filter, created_at FROM videos ORDER BY created_at DESC")
        rows = cur.fetchall()
    
    videos = []
    for row in rows:
        videos.append({
            'id': row[0],
            'original_name': row[1],
            'filter': row[2],
            'created_at': row[3],
            'video_url': url_for('serve_video', video_id=row[0], _external=True),
            'thumbnail_url': url_for('serve_thumb', video_id=row[0], _external=True)
        })
    
    return {'videos': videos}

@app.route("/filters")
def list_filters():
    return {
        "available_filters": [
            {"name": "gray", "description": "Escala de Cinza"},
            {"name": "edges", "description": "Detecção de Bordas"},
            {"name": "pixel", "description": "Pixelização"}
        ]
    }



if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
