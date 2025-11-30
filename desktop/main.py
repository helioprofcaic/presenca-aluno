# -*- coding: utf-8 -*-
import customtkinter as ctk
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
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


# =============================================================================
# --- CLASSE PRINCIPAL DA APLICAÇÃO DESKTOP ---
# =============================================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # --- Configurações Iniciais da Janela ---
        self.title("Sistema de Presença de Alunos")
        
        # Define a geometria da janela para ocupar o lado esquerdo da tela.
        # Formato: "larguraxaltura+posicao_x+posicao_y"
        self.geometry("900x720+0+0") 

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Criação e Configuração do Sistema de Abas (Tabs) ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tab_view.add("Apresentação")
        self.tab_view.add("Ler QR Code")
        self.tab_view.add("Cadastrar Aluno")
        self.tab_view.add("Cadastrar Usuário")
        self.tab_view.add("Importar / Exportar")
        self.tab_view.set("Apresentação")

        # --- Inicialização de Widgets e Variáveis de Controle ---
        # Placeholders for widgets that need to be accessed from other methods
        self.web_qr_label = None
        self.web_url_label = None
        self.apresentacao_qr_frame = None

        self.setup_apresentacao_tab()
        self.setup_ler_qrcode_tab()
        self.setup_cadastrar_aluno_tab()
        self.setup_cadastrar_usuario_tab()
        self.setup_importar_exportar_tab()
        
        # Cooldown para evitar leituras de QR code repetidas rapidamente
        self.last_qr_time = 0
        self.qr_cooldown = 3  # Increased cooldown

        # Variáveis para controle da câmera e multithreading
        self.cap = None # Objeto da câmera
        self.camera_running = False # Controla se a câmera está ativamente lendo frames
        self.camera_thread = None # Thread que gerencia a câmera
        self.queue = queue.Queue(maxsize=1)

        # Inicia a câmera em segundo plano para uma abertura mais rápida depois
        self.pre_initialize_camera()
        # --- Associações de Eventos (Bindings) ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.tab_view.configure(command=self.on_tab_change)
        
        self.on_tab_change()

        # --- Carregamento de Dados Iniciais ---
        self.class_codes = {}
        self.load_class_data()
        
        self.logged_in_user_token = None # Store token after professor login

    # =============================================================================
    # --- UTILITÁRIOS DE REDE E IMAGEM ---
    # =============================================================================
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

    # =============================================================================
    # --- CONFIGURAÇÃO DAS ABAS DA INTERFACE ---
    # =============================================================================
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

    # =============================================================================
    # --- GERENCIAMENTO DE EVENTOS E ESTADO DA APLICAÇÃO ---
    # =============================================================================
    def on_tab_change(self):
        """Callback executado ao trocar de aba para iniciar ou parar a câmera."""
        selected_tab = self.tab_view.get()
        if selected_tab == "Ler QR Code":
            self.start_video()
        else:
            self.stop_video()

    # =============================================================================
    # --- LÓGICA DE CAPTURA DE VÍDEO (MULTITHREADING) ---
    # =============================================================================
    def pre_initialize_camera(self):
        """Inicializa a câmera em uma thread para que ela abra mais rápido quando for necessária."""
        if self.camera_thread is None:
            self.camera_thread = threading.Thread(target=self.video_stream_worker)
            self.camera_thread.daemon = True
            self.camera_thread.start()

    def start_video(self):
        """Ativa a leitura de frames da câmera e inicia a atualização da GUI."""
        if not self.camera_running:
            self.camera_running = True
            self.update_gui()

    def stop_video(self):
        """Desativa a leitura de frames da câmera."""
        self.camera_running = False
        self.video_label.configure(image=None, text="A câmera será iniciada na aba 'Ler QR Code'.")

    def video_stream_worker(self):
        """Worker que roda em uma thread separada para gerenciar a câmera."""
        try:
            # Força o uso do backend MSMF (Media Foundation) no Windows.
            # Isso é mais estável que o DSHOW padrão e resolve muitos problemas de inicialização.
            self.cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
            
            if not self.cap.isOpened():
                # Se a câmera falhar, coloca um 'sinal' de erro na fila.
                self.queue.put((None, "ERROR_CAM"))
                return

            while True: # O loop da thread agora é infinito, controlado pelo fechamento do app
                if self.camera_running: # Só processa se a câmera estiver "ativa"
                    if self.cap is None or not self.cap.isOpened():
                        break
                    ret, frame = self.cap.read()
                    if not ret:
                        time.sleep(0.1)
                        continue

                    # Decodifica apenas QR Codes para evitar warnings de outros formatos (ex: PDF417)
                    decoded_objects = decode(frame, symbols=[ZBarSymbol.QRCODE])
                    if decoded_objects:
                        for obj in decoded_objects:
                            (x, y, w, h) = obj.rect
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    try:
                        self.queue.put_nowait((frame, decoded_objects))
                    except queue.Full:
                        pass
                else:
                    # Se a câmera não estiver em uso, a thread "dorme" para não consumir CPU
                    time.sleep(0.1)
        finally:
            # Garante que a câmera seja liberada se a thread morrer por algum motivo
            if self.cap is not None:
                self.cap.release()

    def update_gui(self):
        if not self.camera_running: return
        try:
            frame, decoded_objects = self.queue.get_nowait()

            # Verifica o sinal de erro da câmera
            if decoded_objects == "ERROR_CAM":
                self.video_label.configure(text="Erro: Não foi possível acessar a câmera.", text_color="red")
                self.stop_video()
                return

            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            ctk_img = ctk.CTkImage(light_image=img, size=(self.cap.get(3), self.cap.get(4)))
            self.video_label.configure(image=ctk_img)
            self.video_label.image = ctk_img

            current_time = time.time()
            if decoded_objects and (current_time - self.last_qr_time > self.qr_cooldown):
                for obj in decoded_objects:
                    qr_data = obj.data.decode('utf-8')
                    # NÃO execute o processamento pesado na thread da GUI.
                    # Inicie uma nova thread para isso.
                    processing_thread = threading.Thread(target=self._process_qr_in_thread, args=(qr_data,))
                    processing_thread.daemon = True
                    processing_thread.start()
                    
                    self.last_qr_time = current_time
                    self.after(3000, self.reset_status_label)
                    break
        except queue.Empty:
            pass
        finally:
            # Garante que o loop de atualização da GUI continue
            self.after(20, self.update_gui)

    # =============================================================================
    # --- PROCESSAMENTO DE DADOS E LÓGICA DE NEGÓCIO ---
    # =============================================================================
    def _process_qr_in_thread(self, ra):
        """
        Processa o QR code em uma thread separada para não bloquear a interface.
        """
        try:
            # 1. Tenta encontrar um aluno pelo RA/INEP lido do QR Code
            student = db.get_student_by_identifier(ra)
            if student:
                # Se encontrou o aluno, registra a presença
                tipo_registro, status_detalhado = db.add_attendance_record(student['id'])
                if tipo_registro:
                    feedback_msg = f"{status_detalhado}: {student['nome']}"
                    self.status_label.configure(text=feedback_msg, text_color="green")
                else:
                    self.status_label.configure(text=f"Fora do horário de registro para {student['nome']}", text_color="orange")
            else:
                # 2. Se não encontrou um aluno, verifica se é um usuário (professor/admin)
                user = db.get_user_by_username(ra)
                if user and user['role'] in ['professor', 'admin']:
                    # Lógica futura para login de professor pode ser adicionada aqui
                    self.status_label.configure(text=f"QR Code de usuário: {user['username']}", text_color="cyan")
                else:
                    # 3. Se não for nem aluno nem usuário, o QR Code é inválido
                    self.status_label.configure(text=f"QR Code não reconhecido: {ra}", text_color="red")
        
        except Exception as e:
            self.status_label.configure(text=f"Erro ao processar QR Code: {e}", text_color="red")

    def update_mobile_login_qr(self):
        """Atualiza o QR Code da aba 'Apresentação' para um QR de login de professor."""
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
        """Reseta a label de status para a mensagem padrão."""
        self.status_label.configure(text="Aguardando leitura...", text_color=self.status_label.cget("text_color_disabled"))

    def import_students_from_json(self):
        """
        Abre uma janela para o usuário selecionar arquivos JSON e os importa.
        """
        # Abre a janela de diálogo para selecionar um ou mais arquivos JSON
        filepaths = ctk.filedialog.askopenfilenames(
            title="Selecione os arquivos JSON das turmas",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        # Se o usuário cancelar a seleção, não faz nada
        if not filepaths:
            self.import_status_label.configure(text="Importação cancelada.", text_color="orange")
            return

        qrcodes_dir = Path("qrcodes")
        qrcodes_dir.mkdir(exist_ok=True)
        imported_count = 0
        updated_count = 0
        errors = []

        for filepath in filepaths:
            json_file = Path(filepath)
            if json_file.name == "turmas-com-disciplinas.json": # Pula o arquivo de configuração de turmas
                continue
            codigo_turma_from_file = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    students_data = json.load(f)
                for student_data in students_data:
                    nome = student_data.get('nome')
                    ra = str(student_data.get('ra'))
                    inep = str(student_data.get('inep')) if student_data.get('inep') else None

                    if not nome or not ra:
                        errors.append(f"Arquivo {json_file.name}: Dados incompletos.")
                        continue
                    existing_student = db.get_student_by_ra(ra)
                    if not existing_student:
                        db.add_student(ra, nome, codigo_turma_from_file, inep=inep)
                        imported_count += 1
                    else:
                        if existing_student['codigo_turma'] != codigo_turma_from_file:
                            db.update_student(ra, {'codigo_turma': codigo_turma_from_file, 'inep': inep}) # Função de update genérica seria ideal
                        updated_count += 1
                    
                    # **NOVO**: Garante que um usuário seja criado para o aluno poder logar na web.
                    # O RA será o usuário e a senha padrão. A função add_user já evita duplicatas.
                    db.add_user(ra, ra, "aluno")

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

    # =============================================================================
    # --- FINALIZAÇÃO DA APLICAÇÃO ---
    # =============================================================================
    def on_closing(self):
        """Callback para garantir que a câmera seja liberada ao fechar a janela."""
        self.camera_running = False # Para a leitura de frames
        if self.camera_thread is not None:
            # A thread é daemon, então não precisamos de join, mas liberamos a câmera explicitamente
            if self.cap is not None:
                self.cap.release()
        self.destroy()

# =============================================================================
# --- PONTO DE ENTRADA DA APLICAÇÃO DESKTOP ---
# =============================================================================
def start_desktop_app():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    # Inicia a aplicação se o script for executado diretamente.
    start_desktop_app()
