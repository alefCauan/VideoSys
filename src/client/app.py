import tkinter as tk
from tkinter import filedialog, ttk
import requests
from PIL import Image, ImageTk, ImageDraw
import io
import os
import cv2

class VideoClient:
    def __init__(self, root):
        # Janela principal do Tkinter
        self.root = root
        self.root.title("Cliente de Vídeos")

        self.server_url = "http://10.180.43.186:5000"

        self.original_thumbnails = {}
        self.filtered_thumbnails = {}

        # Botão para seleção de vídeo
        self.select_btn = tk.Button(
            root, text="Selecionar vídeo", command=self.select_video)
        self.select_btn.pack(pady=5)

        # Botão Dropdown de filtros
        self.filter_label = tk.Label(root, text="Escolha o filtro:")
        self.filter_label.pack()
        self.filter_combo = ttk.Combobox(
            root, values=["gray", "edges", "pixel"])
        self.filter_combo.current(0)
        self.filter_combo.pack(pady=5)

        # Botão de envio
        self.upload_btn = tk.Button(
            root, text="Enviar para processamento", command=self.upload_video)

        self.upload_btn.pack(pady=5)

        # Frame do histórico
        self.history_frame = tk.Frame(root)
        self.history_frame.pack(fill="both", expand=True)

        self.history_list = tk.Listbox(self.history_frame, width=50)
        self.history_list.bind("<<ListboxSelect>>", self.on_history_select)
        self.history_list.pack(side="left", fill="y")

        self.thumbnail_label = tk.Label(self.history_frame)
        self.thumbnail_label.pack(side="right", padx=10)

        # Caminho do vídeo
        self.video_path = None

    def create_image(self, color, name, fill):
        img = Image.new("RGB", (200, 150), color=color)
        draw = ImageDraw.Draw(img)
        draw.text((10, 60), f"{name}", fill)
        return img

    def create_thumb(self, img):
        img.thumbnail((150, 150))
        return ImageTk.PhotoImage(img)

    # Seleção de vídeo
    def select_video(self):
        self.video_path = filedialog.askopenfilename(
            filetypes=[("Vídeos", "*.mp4 *.avi *.mkv")])
        if (self.video_path):
            cap = cv2.VideoCapture(self.video_path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                img = Image.fromarray(frame[..., ::-1])  # converte BGR→RGB
            else:
                img = self.create_image("red", "Erro", "white")

            photo = self.create_thumb(img)
            entry_text = f"Selecionado: {self.video_name()}"

            self.save_image(entry_text, self.original_thumbnails, photo)

    def video_name(self):
        return os.path.basename(self.video_path)

    def set_thumbnail_label(self, photo):
        self.thumbnail_label.config(image=photo)
        self.thumbnail_label.image = photo

    def save_image(self, entry_text, dicio, photo):
        self.history_list.insert(tk.END, entry_text)

        # Salvar a thumbnail original
        dicio[entry_text] = photo

        # Exibir a original
        self.set_thumbnail_label(photo)

    # Envio para o servidor

    def upload_video(self):
        if not self.video_path:
            return
        filtro = self.filter_combo.get()

        with open(self.video_path, "rb") as arquivo:
            files = {"video": arquivo}
            data = {"filter": filtro}
            response = requests.post(
                f"{self.server_url}/upload", files=files, data=data)

            if response.status_code != 200:
                print("Erro no upload:", response.text)
                self.history_list.insert(tk.END, "Erro no upload")
                return

        if (response.status_code == 200):
            # Exibe thumbnail
            data = response.json()
            thumb_url = data.get("thumb_url")
            print(f"Thumb url: {thumb_url}")

            if not thumb_url:
                print("⚠️ Resposta não contém thumb_url:", data)
                return

            img_data = requests.get(thumb_url).content
            img = Image.open(io.BytesIO(img_data))

            # Adiciona no histórico
            entry_text = f"{self.video_name()} | {filtro}"
            photo = self.create_thumb(img)

            self.save_image(entry_text, self.filtered_thumbnails, photo)
        else:
            print(response)
            self.history_list.insert(tk.END, "Erro no upload")

    def on_history_select(self, event):
        # Pega índice selecionado
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            entry_text = event.widget.get(index)

            if (entry_text.startswith("Selecionado:")):
                photo = self.original_thumbnails.get(entry_text)
            else:
                photo = self.filtered_thumbnails.get(entry_text)

            if (photo):
                self.set_thumbnail_label(photo)


root = tk.Tk()
app = VideoClient(root)
root.mainloop()
