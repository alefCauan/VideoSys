import os
import uuid
import datetime
import cv2
from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for, jsonify
import shutil

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

# Função para obter duração do vídeo
def get_video_duration(video_path):
    """Retorna a duração do vídeo em formato MM:SS"""
    try:
        video_capture = cv2.VideoCapture(video_path)
        fps = video_capture.get(cv2.CAP_PROP_FPS)
        frame_count = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
        video_capture.release()
        
        if fps > 0:
            duration_seconds = int(frame_count / fps)
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
    except:
        return "00:00"

# --- Rotas ---
@app.route("/", methods=["GET"])
def index():
    with manager.sqlite3.connect(manager.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, original_name, filter, created_at FROM videos ORDER BY created_at DESC")
        rows = cur.fetchall()
    
    # Adicionar duração aos vídeos
    videos_with_duration = []
    for row in rows:
        video_id, original_name, filter_type, created_at = row
        
        # Buscar o caminho do vídeo
        video_path = None
        for root_dir, sub_dirs, files in os.walk(paths.VIDEOS):
            if video_id in root_dir and "video.mp4" in files:
                video_path = os.path.join(root_dir, "video.mp4")
                break
        
        duration = get_video_duration(video_path) if video_path else "00:00"
        videos_with_duration.append((video_id, original_name, filter_type, created_at, duration))
    
    template = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VideoSYS</title>
        <link rel="icon" type="image/png" href="https://i.imgur.com/d4QrTFx.png">
        <link href="https://fonts.googleapis.com/css2?family=Stick+No+Bills:wght@400&display=swap" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Stick No Bills', sans-serif;
                background: #021A1A;
                color: #ffffff;
                padding: 20px;
                height: 100vh;

            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                overflow-y: auto;
                background: rgba(0,0,0,0.6);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.6);
                height: 90vh;
            }

            header {
                display: flex;
                align-items: center; /* centraliza verticalmente */
                justify-content: center; /* centraliza horizontalmente */
                gap: 20px; /* espaço entre logo e título */
                margin-bottom: 40px;
                flex-wrap: wrap; /* para telas pequenas, quebra linha */
            }

            header img {
                width: 120px; /* logo menor */
                height: auto;
            }

            h1 {
                font-size: 72px; /* título menor */
                font-weight: 400;
                color: #fff;
                margin: 0;
            }

            /* Stats cards */
            .stats-section {
                display: flex;
                justify-content: center;
                gap: 30px;
                flex-wrap: wrap;
                margin-bottom: 40px;
            }
            .stat-card {
                background: transparent;
                border: 2px solid white;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                min-width: 150px;
                color: white;
            }
            .stat-number { font-size: 2em; font-weight: bold; display: block; color: white; }
            .stat-label { font-size: 14px; margin-top: 5px; }

            /* Videos grid */
            .videos-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 25px;
            }

            /* Video card estilo YouTube */
            .video-card {
                background: transparent;
                border-radius: 10px;
                position: relative;
                transition: transform 0.2s ease;
            }
            .video-card:hover { transform: translateY(-4px); }

            /* Thumbnail */
            .thumbnail-link {
                position: relative;
                display: block;
                border-radius: 12px;
                overflow: hidden;
            }
            .video-thumbnail {
                width: 100%;
                aspect-ratio: 16/9;
                object-fit: cover;
                border-radius: 12px;
                display: block;
                background: #111;
            }
            .video-duration {
                position: absolute;
                bottom: 6px;
                right: 6px;
                background: rgba(0,0,0,0.8);
                color: #fff;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }

            /* Video info */
            .video-details {
                margin-top: 10px;
            }
            .video-title {
                font-size: 18px;
                font-weight: 400;
                color: #fff;
                margin-bottom: 4px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .video-meta {
                font-size: 14px;
                color: #aaa;
            }

            /* Delete button */
            .delete-button {
                position: absolute;
                top: 8px;
                right: 8px;
                background: rgba(229,62,62,0.85);
                border: none;
                padding: 6px;
                border-radius: 50%;
                cursor: pointer;
                transition: all 0.3s ease;
                color: #fff;
                font-size: 13px;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0;
            }
            .video-card:hover .delete-button { opacity: 1; }
            .delete-button:hover { background: #c53030; transform: scale(1.1); }

            /* No videos */
            .no-videos {
                text-align: center;
                padding: 60px 20px;
                color: #666;
            }
            .no-videos h2 { margin-bottom: 10px; color: #999; }

            @media (max-width: 768px) {
                h1 { 
                    font-size: 42px; /* título menor em telas pequenas */
                }
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
            <header>
                <img src="https://i.imgur.com/d4QrTFx.png" alt="Logo" class="logo">
                <h1>Galeria de Vídeos</h1>
            </header>

            {% if videos_with_duration %}
                <!-- Stats -->
                <div class="stats-section">
                    <div class="stat-card">
                        <span class="stat-number">{{ videos_with_duration|length }}</span>
                        <div class="stat-label">Total de Vídeos</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{{ videos_with_duration|selectattr('2', 'equalto', 'gray')|list|length }}</span>
                        <div class="stat-label">Escala de Cinza</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{{ videos_with_duration|selectattr('2', 'equalto', 'edges')|list|length }}</span>
                        <div class="stat-label">Detecção de Bordas</div>
                    </div>
                    <div class="stat-card">
                        <span class="stat-number">{{ videos_with_duration|selectattr('2', 'equalto', 'pixel')|list|length }}</span>
                        <div class="stat-label">Pixelizados</div>
                    </div>
                </div>

                <!-- Videos grid -->
                <div class="videos-grid">
                    {% for id, original_name, filter, created_at, duration in videos_with_duration %}
                        <div class="video-card">
                            <!-- Thumbnail -->
                            <a href="{{ url_for('serve_video', video_id=id) }}" class="thumbnail-link">
                                <img src="{{ url_for('serve_thumb', video_id=id) }}" 
                                    alt="Thumbnail do vídeo {{ original_name }}" 
                                    class="video-thumbnail"
                                    onerror="this.src='https://via.placeholder.com/320x180?text=Sem+Thumb'">
                                <span class="video-duration">{{ duration }}</span>
                            </a>

                            <!-- Informações -->
                            <div class="video-details">
                                <div class="video-title">{{ original_name }}</div>
                                <div class="video-meta">
                                    {% if filter == 'gray' %}Escala de Cinza
                                    {% elif filter == 'edges' %}Detecção de Bordas
                                    {% elif filter == 'pixel' %}Pixelização
                                    {% endif %}
                                </div>
                            </div>

                            <!-- Botão Deletar -->
                            <form action="{{ url_for('delete_video', video_id=id) }}" method="POST" 
                                onsubmit="return confirm('Tem certeza que deseja deletar este vídeo?');">
                                <button type="submit" class="delete-button" title="Deletar vídeo">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </form>
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
    return render_template_string(template, videos_with_duration=videos_with_duration)

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
    output_directory = os.path.join(
        paths.VIDEOS,
        today_date.strftime("%Y"),
        today_date.strftime("%m"),
        today_date.strftime("%d"),
        video_uuid
    )
    os.makedirs(output_directory, exist_ok=True)

    # --- Salvar original ---
    original_dir = os.path.join(output_directory, "original")
    os.makedirs(original_dir, exist_ok=True)
    original_ext = os.path.splitext(uploaded_file.filename)[1]
    original_dest = os.path.join(original_dir, f"original{original_ext}")
    shutil.move(temp_file_path, original_dest)

    # --- Gerar processado ---
    processed_dir = os.path.join(output_directory, "processed", selected_filter)
    os.makedirs(processed_dir, exist_ok=True)
    processed_dest = os.path.join(processed_dir, f"video_{selected_filter}{original_ext}")
    process_video(original_dest, processed_dest, selected_filter)

    # --- Thumbnail ---
    thumbs_dir = os.path.join(output_directory, "thumbs")
    os.makedirs(thumbs_dir, exist_ok=True)
    thumb_path = os.path.join(thumbs_dir, "thumb.jpg")
    generate_thumbnail(processed_dest, thumb_path)

    # --- Metadados ---
    result = manager.save_meta_json(
        video_uuid,
        uploaded_file.filename,
        selected_filter,
        original_dest,
        processed_dest,
        thumb_path,
        output_directory
    )

    # --- Banco ---
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
        <link href="https://fonts.googleapis.com/css2?family=Stick+No+Bills:wght@400&display=swap" rel="stylesheet">
        <title>{{ video[1] }} - Video Processor</title>
        <style>
            body {
                margin: 0;
                padding: 20px;
                background: #000000;
                color: white;
                font-family: 'Stick No Bills', sans-serif;
                color: #ffffff; 
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

            delete-button {
                background: #e53e3e;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                transition: background 0.3s ease;
            }
            delete-button:hover {
                background: #c53030;
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
    
    with manager.sqlite3.connect(manager.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT path_processed FROM videos WHERE id = ?", (video_id,))
        row = cur.fetchone()
        
        if not row:
            return "Vídeo não encontrado", 404

        video_path = row[0]

        # Remove do banco
        cur.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()

    # Move somente o arquivo de vídeo para a lixeira
    if video_path and os.path.exists(video_path):
        trash_dir = paths.TRASH   
        os.makedirs(trash_dir, exist_ok=True)

        trash_target = os.path.join(trash_dir, os.path.basename(video_path))

        # Se já existir um arquivo com o mesmo nome, adiciona sufixo
        counter = 1
        while os.path.exists(trash_target):
            name, ext = os.path.splitext(os.path.basename(video_path))
            trash_target = os.path.join(trash_dir, f"{name}_{counter}{ext}")
            counter += 1

        shutil.move(video_path, trash_target)

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
