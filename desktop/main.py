# -*- coding: utf-8 -*-
import customtkinter as ctk
import cv2
from pyzbar.pyzbar import decode
from PIL import Image, ImageTk
import threading
import queue
import time
import qrcode
import os
import json
from pathlib import Path
import socket
import database as db
import webbrowser
import requests
from desktop.page_create import PaginaCadastro
from desktop.page_user_create import PaginaCadastroUsuario


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Presença de Alunos")
        self.geometry("900x720")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tab_view.add("Apresentação")
        self.tab_view.add("Ler QR Code")
        self.tab_view.add("Cadastrar Aluno")
        self.tab_view.add("Cadastrar Usuário")
        self.tab_view.add("Importar / Exportar")
        self.tab_view.set("Apresentação")

        # Placeholders for widgets that need to be accessed from other methods
        self.web_qr_label = None
        self.web_url_label = None
        self.apresentacao_qr_frame = None

        self.setup_apresentacao_tab()
        self.setup_ler_qrcode_tab()
        self.setup_cadastrar_aluno_tab()
        self.setup_cadastrar_usuario_tab()
        self.setup_importar_exportar_tab()
        
        self.last_qr_time = 0
        self.qr_cooldown = 3  # Increased cooldown

        self.cap = None
        self.running = False
        self.queue = queue.Queue(maxsize=1)
        self.thread = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.tab_view.configure(command=self.on_tab_change)
        
        self.on_tab_change()

        self.class_codes = {}
        self.load_class_data()
        
        self.logged_in_user_token = None # Store token after professor login

    def get_local_ip(self):
        """Tries to get the local IP address of the machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        IP = '127.0.0.1'
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            try:
                IP = socket.gethostbyname(socket.gethostname())
            except Exception:
                IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def generate_qr_code_image(self, data, size=200):
        """Generates a CTkImage object from the given data."""
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        return ctk.CTkImage(light_image=img, size=(size, size))

    def setup_apresentacao_tab(self):
        tab = self.tab_view.tab("Apresentação")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        title_label = ctk.CTkLabel(tab, text="Bem-vindo ao Sistema de Presença", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        description_text = "Para a versão web, escaneie o QR Code abaixo com seu celular.\nCertifique-se de que seu computador e celular estão na mesma rede Wi-Fi."
        description_label = ctk.CTkLabel(tab, text=description_text, font=ctk.CTkFont(size=14), justify="center")
        description_label.grid(row=1, column=0, padx=20, pady=10, sticky="n")

        self.apresentacao_qr_frame = ctk.CTkFrame(tab)
        self.apresentacao_qr_frame.grid(row=2, column=0, padx=20, pady=20)

        ctk.CTkLabel(self.apresentacao_qr_frame, text="Acessar Versão Web", font=ctk.CTkFont(size=16)).pack(pady=(10, 5))

        try:
            web_url = f"http://{self.get_local_ip()}:5000"
            print(f"URL para o QR Code da Web: {web_url}")

            ctk_img = self.generate_qr_code_image(web_url)
            
            self.web_qr_label = ctk.CTkLabel(self.apresentacao_qr_frame, image=ctk_img, text="")
            self.web_qr_label.pack(padx=10, pady=10)
            
            self.web_url_label = ctk.CTkLabel(self.apresentacao_qr_frame, text=web_url, font=ctk.CTkFont(size=12))
            self.web_url_label.pack(pady=(0, 10))

        except Exception as e:
            error_label = ctk.CTkLabel(self.apresentacao_qr_frame, text=f"Erro ao gerar QR Code da web:\n{e}", text_color="red")
            error_label.pack(padx=10, pady=10)

    def load_class_data(self):
        class_data_path = Path("data/turmas-com-disciplinas.json")
        if class_data_path.exists():
            try:
                with open(class_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for class_info in data:
                        self.class_codes[class_info['codigoTurma']] = class_info['nomeTurma']
                print(f"Turmas carregadas: {self.class_codes}")
            except Exception as e:
                print(f"Erro ao carregar dados das turmas: {e}")
        else:
            print(f"Arquivo de dados das turmas não encontrado: {class_data_path}")

    def setup_ler_qrcode_tab(self):
        tab = self.tab_view.tab("Ler QR Code")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.video_label = ctk.CTkLabel(tab, text="A câmera será iniciada nesta aba.")
        self.video_label.grid(row=0, column=0, sticky="nsew")
        self.status_label = ctk.CTkLabel(tab, text="Aguardando leitura...", font=ctk.CTkFont(size=20))
        self.status_label.grid(row=1, column=0, pady=10)

    def setup_cadastrar_aluno_tab(self):
        """Inicializa a página de cadastro a partir do módulo page_create."""
        tab = self.tab_view.tab("Cadastrar Aluno")
        self.create_page = PaginaCadastro(tab, self)

    def setup_cadastrar_usuario_tab(self):
        """Inicializa a página de cadastro de usuário."""
        tab = self.tab_view.tab("Cadastrar Usuário")
        self.user_create_page = PaginaCadastroUsuario(tab)

    def setup_importar_exportar_tab(self):
        tab = self.tab_view.tab("Importar / Exportar")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        import_button = ctk.CTkButton(tab, text="Importar Alunos de JSON", command=self.import_students_from_json)
        import_button.grid(row=0, column=0, padx=20, pady=20)
        self.import_status_label = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=14))
        self.import_status_label.grid(row=1, column=0, padx=20, pady=10)

    def on_tab_change(self):
        selected_tab = self.tab_view.get()
        if selected_tab == "Ler QR Code":
            self.start_video()
        else:
            self.stop_video()

    def start_video(self):
        if not self.running:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.video_label.configure(text="Erro: Não foi possível acessar a câmera.")
                return
            self.running = True
            self.thread = threading.Thread(target=self.video_stream_worker)
            self.thread.daemon = True
            self.thread.start()
            self.update_gui()

    def stop_video(self):
        if self.running:
            self.running = False
            if self.thread is not None:
                self.thread.join(timeout=1.0)
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.video_label.configure(image=None, text="A câmera será iniciada na aba 'Ler QR Code'.")

    def video_stream_worker(self):
        while self.running:
            if self.cap is None: break
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            decoded_objects = decode(frame)
            if decoded_objects:
                for obj in decoded_objects:
                    (x, y, w, h) = obj.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            try:
                self.queue.put_nowait((frame, decoded_objects))
            except queue.Full:
                pass

    def update_gui(self):
        if not self.running: return
        try:
            frame, decoded_objects = self.queue.get_nowait()
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            ctk_img = ctk.CTkImage(light_image=img, size=(self.cap.get(3), self.cap.get(4)))
            self.video_label.configure(image=ctk_img)
            self.video_label.image = ctk_img

            current_time = time.time()
            if decoded_objects and (current_time - self.last_qr_time > self.qr_cooldown):
                for obj in decoded_objects:
                    qr_data = obj.data.decode('utf-8')
                    self.process_qr_code(qr_data)
                    self.last_qr_time = current_time
                    self.after(3000, self.reset_status_label)
                    break
        except queue.Empty:
            pass
        finally:
            self.after(20, self.update_gui)

    def process_qr_code(self, ra):
        api_url = "http://127.0.0.1:5000/api/generate-login-token"
        try:
            response = requests.post(api_url, json={"ra": ra})
            if response.status_code == 200:
                data = response.json()
                role = data.get("role")
                nome = data.get("nome", "Desconhecido")

                if role == "professor" and "token" in data:
                    self.logged_in_user_token = data["token"]
                    self.status_label.configure(text=f"Login de Professor: {nome}", text_color="cyan")
                    login_url = f"http://127.0.0.1:5000/login-with-token?token={self.logged_in_user_token}"
                    webbrowser.open(login_url)
                    self.update_mobile_login_qr()
                    self.tab_view.set("Apresentação")

                elif role == "aluno":
                    student = db.get_student_by_ra(ra)
                    if student:
                        db.add_attendance_record(student['id'], "Presente")
                        self.status_label.configure(text=f"Presença Confirmada: {student['nome']}", text_color="green")
                    else:
                        self.status_label.configure(text=f"Aluno não encontrado no DB local: {ra}", text_color="red")
                else:
                    self.status_label.configure(text=f"Usuário '{nome}' não é professor.", text_color="orange")

            elif response.status_code == 404:
                self.status_label.configure(text=f"Usuário ou Aluno não encontrado: {ra}", text_color="red")
            else:
                self.status_label.configure(text=f"Erro na API: {response.status_code}", text_color="red")

        except requests.exceptions.ConnectionError:
            self.status_label.configure(text="Erro: Não foi possível conectar ao servidor web.", text_color="red")
        except Exception as e:
            self.status_label.configure(text=f"Erro inesperado: {e}", text_color="red")

    def update_mobile_login_qr(self):
        if not self.logged_in_user_token:
            return

        if self.web_qr_label and self.web_url_label:
            try:
                mobile_login_url = f"http://{self.get_local_ip()}:5000/login-with-token?token={self.logged_in_user_token}"
                ctk_img = self.generate_qr_code_image(mobile_login_url)
                self.web_qr_label.configure(image=ctk_img)
                self.web_qr_label.image = ctk_img
                self.web_url_label.configure(text=mobile_login_url)
                for widget in self.apresentacao_qr_frame.winfo_children():
                    if isinstance(widget, ctk.CTkLabel) and "Acessar Versão Web" in widget.cget("text"):
                        widget.configure(text="Login Móvel para Professor")
                        break
            except Exception as e:
                self.web_url_label.configure(text=f"Erro ao gerar QR Code de login móvel: {e}")

    def reset_status_label(self):
        self.status_label.configure(text="Aguardando leitura...", text_color=self.status_label.cget("text_color_disabled"))

    def import_students_from_json(self):
        data_dir = Path("data")
        if not data_dir.exists():
            self.import_status_label.configure(text="Erro: Pasta 'data' não encontrada.", text_color="red")
            return
        qrcodes_dir = Path("qrcodes")
        qrcodes_dir.mkdir(exist_ok=True)
        imported_count = 0
        updated_count = 0
        errors = []
        for json_file in data_dir.glob("*.json"):
            if json_file.name == "turmas-com-disciplinas.json":
                continue
            codigo_turma_from_file = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    students_data = json.load(f)
                for student_data in students_data:
                    nome = student_data.get('nome')
                    ra = str(student_data.get('ra'))
                    if not nome or not ra:
                        errors.append(f"Arquivo {json_file.name}: Dados incompletos.")
                        continue
                    existing_student = db.get_student_by_ra(ra)
                    if not existing_student:
                        db.add_student(ra, nome, codigo_turma_from_file)
                        imported_count += 1
                    else:
                        if existing_student['codigo_turma'] != codigo_turma_from_file:
                            db.update_student_class(ra, codigo_turma_from_file)
                        updated_count += 1
                    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
                    qr.add_data(ra)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    qr_filename = qrcodes_dir / f"turma_{codigo_turma_from_file}_ra_{ra}.png"
                    img.save(qr_filename)
            except json.JSONDecodeError:
                errors.append(f"Erro de JSON em {json_file.name}.")
            except Exception as e:
                errors.append(f"Erro em {json_file.name}: {e}")
        status_message = f"Importação: {imported_count} novos, {updated_count} atualizados."
        if errors:
            status_message += f" Erros: {len(errors)}."
            self.import_status_label.configure(text=status_message, text_color="orange")
            for err in errors:
                print(err)
        else:
            self.import_status_label.configure(text=status_message, text_color="green")

    def on_closing(self):
        self.stop_video()
        self.destroy()

def start_desktop_app():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    start_desktop_app()
