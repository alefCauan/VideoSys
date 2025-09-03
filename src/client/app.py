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
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # self.server_url = "http://10.180.43.186:5000"
        self.server_url = "http://10.180.43.11:5000"

        self.original_thumbnails = {}
        self.filtered_thumbnails = {}
        self.video_path = None

        self.setup_ui()

    def setup_ui(self):
        # Configurar o grid principal
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Frame superior para controles
        self.create_control_frame()

        # Frame principal dividido
        self.create_main_content()

    def create_control_frame(self):
        """Cria o frame superior com os controles"""
        control_frame = tk.Frame(self.root, bg="#f0f0f0", padx=10, pady=10)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        control_frame.columnconfigure(1, weight=1)

        # Título
        title_label = tk.Label(control_frame, text="Cliente de Processamento de Vídeos",
                               font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Frame para seleção de vídeo
        video_frame = tk.LabelFrame(control_frame, text="Seleção de Vídeo",
                                    font=("Arial", 10, "bold"), padx=10, pady=5)
        video_frame.grid(row=1, column=0, sticky="ew", padx=(0, 5))

        self.select_btn = tk.Button(video_frame, text="📁 Selecionar Vídeo",
                                    command=self.select_video,
                                    font=("Arial", 10),
                                    bg="#4CAF50", fg="white",
                                    padx=20, pady=5)
        self.select_btn.pack(pady=5)

        self.video_label = tk.Label(video_frame, text="Nenhum vídeo selecionado",
                                    font=("Arial", 9), fg="#666")
        self.video_label.pack()

        # Frame para filtros
        filter_frame = tk.LabelFrame(control_frame, text="Configurações",
                                     font=("Arial", 10, "bold"), padx=10, pady=5)
        filter_frame.grid(row=1, column=1, sticky="ew", padx=5)

        tk.Label(filter_frame, text="Filtro:", font=("Arial", 9)).pack()
        self.filter_combo = ttk.Combobox(filter_frame, values=["gray", "edges", "pixel"],
                                         state="readonly", width=15)
        self.filter_combo.current(0)
        self.filter_combo.pack(pady=5)

        # Frame para ação
        action_frame = tk.LabelFrame(control_frame, text="Processamento",
                                     font=("Arial", 10, "bold"), padx=10, pady=5)
        action_frame.grid(row=1, column=2, sticky="ew", padx=(5, 0))

        self.upload_btn = tk.Button(action_frame, text="🚀 Processar Vídeo",
                                    command=self.upload_video,
                                    font=("Arial", 10),
                                    bg="#2196F3", fg="white",
                                    padx=20, pady=5)
        self.upload_btn.pack(pady=5)

        # Status
        self.status_label = tk.Label(action_frame, text="Pronto",
                                     font=("Arial", 9), fg="#666")
        self.status_label.pack()

    def create_main_content(self):
        """Cria o conteúdo principal com histórico e preview"""
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Frame do histórico (lado esquerdo)
        self.create_history_frame(main_frame)

        # Frame do preview (lado direito)
        self.create_preview_frame(main_frame)

    def create_history_frame(self, parent):
        """Cria o frame do histórico"""
        history_frame = tk.LabelFrame(parent, text="Histórico de Processamentos",
                                      font=("Arial", 10, "bold"), padx=10, pady=5)
        history_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        # Listbox com scrollbar
        list_frame = tk.Frame(history_frame)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.history_list = tk.Listbox(list_frame,
                                       font=("Arial", 10),
                                       selectmode=tk.SINGLE,
                                       bg="white",
                                       relief="sunken",
                                       bd=1)
        self.history_list.grid(row=0, column=0, sticky="nsew")
        self.history_list.bind("<<ListboxSelect>>", self.on_history_select)

        scrollbar = tk.Scrollbar(
            list_frame, orient="vertical", command=self.history_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.history_list.configure(yscrollcommand=scrollbar.set)

        # Botões de ação
        button_frame = tk.Frame(history_frame)
        button_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        clear_btn = tk.Button(button_frame, text="🗑️ Limpar Histórico",
                              command=self.clear_history,
                              font=("Arial", 9),
                              bg="#f44336", fg="white")
        clear_btn.pack(side=tk.RIGHT)

    def create_preview_frame(self, parent):
        """Cria o frame de preview"""
        preview_frame = tk.LabelFrame(parent, text="Preview",
                                      font=("Arial", 10, "bold"), padx=10, pady=5)
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        # Container para centralizar a imagem
        image_container = tk.Frame(
            preview_frame, bg="white", relief="sunken", bd=1)
        image_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.thumbnail_label = tk.Label(image_container,
                                        text="Selecione um vídeo para ver o preview",
                                        font=("Arial", 12),
                                        fg="#888",
                                        bg="white",
                                        compound="center")
        self.thumbnail_label.pack(expand=True, fill="both")

        # Info frame
        info_frame = tk.Frame(preview_frame)
        info_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        self.info_label = tk.Label(info_frame, text="",
                                   font=("Arial", 9), fg="#666")
        self.info_label.pack()

    def create_image(self, color, name, fill):
        img = Image.new("RGB", (200, 150), color=color)
        draw = ImageDraw.Draw(img)
        draw.text((10, 60), f"{name}", fill)
        return img

    def create_thumb(self, img):
        # Criar thumbnail mantendo proporção
        img_copy = img.copy()
        img_copy.thumbnail((400, 300), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img_copy)

    def select_video(self):
        self.video_path = filedialog.askopenfilename(
            title="Selecionar Vídeo",
            filetypes=[("Vídeos", "*.mp4 *.avi *.mkv *.mov"), ("Todos", "*.*")])

        if self.video_path:
            self.update_status("Carregando preview do vídeo...")

            # Atualizar label do vídeo selecionado
            video_name = self.video_name()
            self.video_label.config(text=f"📹 {video_name}", fg="#2196F3")

            try:
                cap = cv2.VideoCapture(self.video_path)
                ret, frame = cap.read()
                cap.release()

                if ret:
                    img = Image.fromarray(frame[..., ::-1])  # converte BGR→RGB
                    self.update_status("Vídeo carregado com sucesso")
                else:
                    img = self.create_image("red", "Erro ao carregar", "white")
                    self.update_status("Erro ao carregar o vídeo", error=True)

                photo = self.create_thumb(img)
                entry_text = f"📁 Selecionado: {video_name}"

                self.save_image(entry_text, self.original_thumbnails, img, f"Arquivo: {video_name}")
                # self.resize_and_set_thumbnail(img)
                # self.original_thumbnails[entry_text] = img
                # self.history_list.insert(tk.END, entry_text)
                # self.info_label.config(text=f"Arquivo: {video_name}")

            except Exception as e:
                self.update_status(f"Erro: {str(e)}", error=True)
                img = self.create_image("red", "Erro", "white")
                photo = self.create_thumb(img)
                self.set_thumbnail_label(photo)

    def video_name(self):
        return os.path.basename(self.video_path) if self.video_path else ""

    def set_thumbnail_label(self, photo):
        self.thumbnail_label.config(image=photo, text="")
        self.thumbnail_label.image = photo

    def save_image(self, entry_text, dicio, photo, info_label):
        # Adicionar ao histórico sem duplicatas
        items = self.history_list.get(0, tk.END)

        if entry_text not in items:
            self.history_list.insert(tk.END, entry_text)

        # Salvar a thumbnail
        self.resize_and_set_thumbnail(photo)
        dicio[entry_text] = photo
        # self.history_list.insert(tk.END, entry_text)
        self.info_label.config(text=info_label)

        # Exibir e selecionar o item
        self.history_list.selection_clear(0, tk.END)
        self.history_list.selection_set(tk.END)
        self.history_list.see(tk.END)

    def upload_video(self):
        if not self.video_path:
            self.update_status("Selecione um vídeo primeiro!", error=True)
            return

        filtro = self.filter_combo.get()
        self.update_status("Enviando vídeo para processamento...")

        # Desabilitar botão durante upload
        self.upload_btn.config(state="disabled", text="⏳ Processando...")

        try:
            with open(self.video_path, "rb") as arquivo:
                files = {"video": arquivo}
                data = {"filter": filtro}
                response = requests.post(
                    f"{self.server_url}/upload", files=files, data=data, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    thumb_url = data.get("thumb_url")

                    if thumb_url:
                        img_data = requests.get(thumb_url).content
                        img = Image.open(io.BytesIO(img_data))

                        entry_text = f"🎬 {self.video_name()} | Filtro: {filtro}"

                        self.save_image(entry_text, self.filtered_thumbnails, img, f"Processado com filtro: {filtro}")

                        # self.resize_and_set_thumbnail(img)
                        # self.filtered_thumbnails[entry_text] = img
                        # self.history_list.insert(tk.END, entry_text)
                        # self.info_label.config(
                        #     text=f"Processado com filtro: {filtro}")

                        self.update_status(
                            "Processamento concluído com sucesso!")
                    else:
                        self.update_status(
                            "Resposta inválida do servidor", error=True)
                else:
                    self.update_status(
                        f"Erro no servidor: {response.status_code}", error=True)

        except requests.exceptions.Timeout:
            self.update_status(
                "Timeout: Servidor demorou para responder", error=True)
        except requests.exceptions.ConnectionError:
            self.update_status("Erro de conexão com o servidor", error=True)
        except Exception as e:
            self.update_status(f"Erro inesperado: {str(e)}", error=True)
        finally:
            # Reabilitar botão
            self.upload_btn.config(state="normal", text="🚀 Processar Vídeo")

    def update_status(self, message, error=False):
        """Atualiza a mensagem de status"""
        color = "#f44336" if error else "#4CAF50"
        self.status_label.config(text=message, fg=color)
        # Auto-limpar status após 5 segundos
        self.root.after(5000, lambda: self.status_label.config(
            text="Pronto", fg="#666"))

    def on_history_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            entry_text = event.widget.get(index)

            if entry_text.startswith("📁 Selecionado:"):
                photo = self.original_thumbnails.get(entry_text)
                self.info_label.config(text="Vídeo original selecionado")
            else:
                photo = self.filtered_thumbnails.get(entry_text)
                filter_name = entry_text.split(
                    "Filtro: ")[-1] if "Filtro: " in entry_text else "Processado"
                self.info_label.config(
                    text=f"Vídeo processado - {filter_name}")

            if photo:
                self.resize_and_set_thumbnail(photo)
                self.current_img = photo

    def clear_history(self):
        """Limpa o histórico"""
        self.history_list.delete(0, tk.END)
        self.original_thumbnails.clear()
        self.filtered_thumbnails.clear()
        self.thumbnail_label.config(image="", text="Histórico limpo")
        self.info_label.config(text="")

    def resize_and_set_thumbnail(self, img):
        """Redimensiona a imagem para ocupar o espaço do thumbnail_label"""
        container_width = self.thumbnail_label.winfo_width()
        container_height = self.thumbnail_label.winfo_height()

        if container_width <= 1 or container_height <= 1:
            # Se ainda não foi renderizado, agenda para depois
            self.thumbnail_label.after(
                100, lambda: self.resize_and_set_thumbnail(img))
            return

        # Redimensiona para caber exatamente no espaço
        img_resized = img.resize(
            (container_width, container_height), Image.LANCZOS)

        photo = ImageTk.PhotoImage(img_resized)
        self.set_thumbnail_label(photo)


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoClient(root)
    root.mainloop()
