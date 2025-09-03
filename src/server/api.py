import os
import uuid
import datetime
import cv2
from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for

# imports locais
from storage import manager, paths
from filters import grayscale, edges, pixelate

app = Flask(__name__)
manager.init_db()

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
    {% for id, original_name, filter, created_at in rows %}
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

    # metadata + banco
    manager.save_meta_json(
        video_uuid,
        uploaded_file.filename,
        selected_filter,
        output_video_path,
        thumbnail_file_path,
        output_directory
    )

    os.remove(temp_file_path)
    return redirect(url_for("index"))

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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
