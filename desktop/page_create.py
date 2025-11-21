import customtkinter as ctk
from PIL import Image
import qrcode
import database as db

class PaginaCadastro:
    def __init__(self, tab, app):
        self.tab = tab
        self.app = app  # Reference to the main App instance
        self.generated_qr_image = None
        self.last_registered_ra = None
        self.last_registered_turma = None

        self.setup_ui()

    def setup_ui(self):
        """Configura os widgets da aba 'Cadastrar Aluno'."""
        self.tab.grid_columnconfigure(0, weight=1)
        self.tab.grid_columnconfigure(1, weight=2)

        # --- Formulário de Cadastro ---
        form_frame = ctk.CTkFrame(self.tab)
        form_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="Nome do Aluno:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.nome_entry = ctk.CTkEntry(form_frame, width=250)
        self.nome_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="ID do Aluno (RA):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.id_entry = ctk.CTkEntry(form_frame, width=250)
        self.id_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Código da Turma:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.turma_entry = ctk.CTkEntry(form_frame, width=250)
        self.turma_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self.register_button = ctk.CTkButton(form_frame, text="Cadastrar e Gerar QR Code", command=self.register_student)
        self.register_button.grid(row=3, column=0, columnspan=2, padx=10, pady=20)
        
        self.register_status_label = ctk.CTkLabel(form_frame, text="", font=ctk.CTkFont(size=14))
        self.register_status_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

        # --- Visualizador de QR Code ---
        qr_frame = ctk.CTkFrame(self.tab)
        qr_frame.grid(row=0, column=1, rowspan=2, padx=20, pady=20, sticky="nsew")
        qr_frame.grid_rowconfigure(0, weight=1)
        qr_frame.grid_columnconfigure(0, weight=1)
        
        self.qr_code_label = ctk.CTkLabel(qr_frame, text="O QR Code gerado aparecerá aqui.")
        self.qr_code_label.grid(row=0, column=0, sticky="nsew")
        
        self.save_qr_button = ctk.CTkButton(qr_frame, text="Salvar QR Code", command=self.save_qr_code, state="disabled")
        self.save_qr_button.grid(row=1, column=0, padx=10, pady=10)

    def register_student(self):
        """Cadastra um novo aluno e gera seu QR code."""
        nome = self.nome_entry.get().strip()
        ra = self.id_entry.get().strip()
        codigo_turma = self.turma_entry.get().strip()

        if not nome or not ra or not codigo_turma:
            self.register_status_label.configure(text="Nome, RA e Código da Turma são obrigatórios.", text_color="red")
            return
        
        if codigo_turma not in self.app.class_codes:
            self.register_status_label.configure(text=f"Código da Turma '{codigo_turma}' não encontrado.", text_color="red")
            return

        try:
            # A lógica de cadastro do aluno no banco de dados
            new_student_id = db.add_student(ra, nome, codigo_turma)
            if new_student_id:
                self.register_status_label.configure(text=f"Aluno '{nome}' cadastrado com sucesso!", text_color="green")
                self.last_registered_ra = ra
                self.last_registered_turma = codigo_turma
                
                # Limpa os campos de entrada após o sucesso
                self.nome_entry.delete(0, 'end')
                self.id_entry.delete(0, 'end')
                self.turma_entry.delete(0, 'end')
            else:
                self.register_status_label.configure(text="RA de aluno já cadastrado.", text_color="orange")
                # Não limpa os campos para que o usuário possa corrigir
                return
        except Exception as e:
            self.register_status_label.configure(text=f"Erro ao salvar no banco de dados: {e}", text_color="red")
            return

        # Geração do QR Code movida para após o cadastro bem-sucedido
        try:
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(ra)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((250, 250), Image.Resampling.LANCZOS)
            
            self.generated_qr_image = img
            ctk_img = ctk.CTkImage(light_image=self.generated_qr_image, size=(250, 250))
            
            self.qr_code_label.configure(image=ctk_img, text="")
            self.qr_code_label.image = ctk_img # Mantém a referência
            self.save_qr_button.configure(state="normal")
        except Exception as e:
            self.register_status_label.configure(text=f"Erro ao gerar QR Code: {e}", text_color="red")

    def save_qr_code(self):
        """Salva a imagem do QR code gerado em um arquivo."""
        if self.generated_qr_image and self.last_registered_ra and self.last_registered_turma:
            filename = f"turma_{self.last_registered_turma}_ra_{self.last_registered_ra}.png"
            filepath = ctk.filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                initialfile=filename,
                title="Salvar QR Code como..."
            )
            if filepath:
                try:
                    self.generated_qr_image.save(filepath)
                    self.register_status_label.configure(text=f"QR Code salvo em {filepath}", text_color="green")
                except Exception as e:
                    self.register_status_label.configure(text=f"Erro ao salvar QR Code: {e}", text_color="red")
        else:
            # Informa ao usuário que não há QR code para salvar ou os dados foram perdidos
            self.register_status_label.configure(text="Nenhum QR Code para salvar ou dados do aluno ausentes.", text_color="orange")
