import tkinter as tk
from tkinter import filedialog, ttk
import requests
from PIL import Image, ImageTk, ImageDraw
import io
import os

class VideoClient:
    def __init__(self, root):
        self.simulada = True

        # Janela principal do Tkinter
        self.root = root
        self.root.title("Cliente de Vídeos")

        self.server_url = "http://127.0.0.1:5000/process_video"

        self.history_thumbnails = {}

        # Botão para seleção de vídeo
        self.select_btn = tk.Button(
            root, text="Selecionar vídeo", command=self.select_video)
        self.select_btn.pack(pady=5)

        # Botão Dropdown de filtros
        self.filter_label = tk.Label(root, text="Escolha o filtro:")
        self.filter_label.pack()
        self.filter_combo = ttk.Combobox(root, values=["filtro1", "filtro2"])
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

    # Seleção de vídeo
    def select_video(self):
        self.video_path = filedialog.askopenfilename(
            filetypes=[("Vídeos", "*.mp4 *.avi *.mkv")])
        if self.video_path:
            self.history_list.insert(
                tk.END, f"Selecionado: {os.path.basename(self.video_path)}")

    # Envio para o servidor
    def upload_video(self):
        if not self.video_path:
            return
        filtro = self.filter_combo.get()
        files = {"video": open(self.video_path, "rb")}

        if (not self.simulada):
            data = {"filter": filtro}
            response = requests.post(self.server_url, files=files, data=data)
        else:
            # Criar thumbnail simulada
            img = Image.new("RGB", (200, 150), color="gray")
            draw = ImageDraw.Draw(img)
            draw.text((10, 60), f"{filtro}", fill="white")

        if (self.simulada or response.status_code == 200):
            # Adiciona no histórico
            entry_text = f"{os.path.basename(self.video_path)} | {filtro}"
            self.history_list.insert(tk.END, entry_text)

            # Exibe thumbnail
            if (not self.simulada):
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))

            img.thumbnail((150, 150))
            photo = ImageTk.PhotoImage(img)
            self.history_thumbnails[entry_text] = photo
            self.thumbnail_label.config(image=photo)
            self.thumbnail_label.image = photo
        else:
            self.history_list.insert(tk.END, "Erro no upload")

    # # Envio para o servidor
    # def upload_video(self):
    #     if not self.video_path:
    #         return
    #     filtro = self.filter_combo.get()
    #     files = {"video": open(self.video_path, "rb")}
    #     data = {"filter": filtro}
    #     response = requests.post(self.server_url, files=files, data=data)
    #     if response.status_code == 200:
    #         # Adiciona no histórico
    #         entry_text = f"{os.path.basename(self.video_path)} | {filtro}"
    #         self.history_list.insert(tk.END, entry_text)

    #         # Exibe thumbnail
    #         img_data = response.content
    #         img = Image.open(io.BytesIO(img_data))
    #         img.thumbnail((150, 150))
    #         photo = ImageTk.PhotoImage(img)
    #         self.thumbnail_label.config(image=photo)
    #         self.thumbnail_label.image = photo
    #     else:
    #         self.history_list.insert(tk.END, "Erro no upload")

    # # Envio simulado para o servidor
    # def mock_upload_video(self):
    #     if not self.video_path:
    #         return
    #     filtro = self.filter_combo.get()

    #     # Criar thumbanil simulada
    #     img = Image.new("RGB", (200, 150), color="gray")
    #     draw = ImageDraw.Draw(img)
    #     draw.text((10, 60), f"{filtro}", fill="white")
    #     img.thumbnail((150, 150))
    #     photo = ImageTk.PhotoImage(img)

    #     # Adicionar no histórico
    #     entry_text = f"{self.video_path.split('/')[-1]} | {filtro}"
    #     self.history_list.insert(tk.END, entry_text)

    #     # Salvar referência da thumbnail
    #     self.history_thumbnails[entry_text] = photo

    #     # Exibir thumbnail
    #     self.thumbnail_label.config(image=photo)
    #     self.thumbnail_label.image = photo

    def on_history_select(self, event):
        # Pega índice selecionado
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            entry_text = event.widget.get(index)
            # Recupera e exibe a thumbnail
            if entry_text in self.history_thumbnails:
                photo = self.history_thumbnails[entry_text]
                self.thumbnail_label.config(image=photo)
                self.thumbnail_label.image = photo


root = tk.Tk()
app = VideoClient(root)
root.mainloop()
