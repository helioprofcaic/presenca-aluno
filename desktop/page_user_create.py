# -*- coding: utf-8 -*-
import customtkinter as ctk
import database as db

class PaginaCadastroUsuario:
    def __init__(self, tab):
        self.tab = tab
        self.setup_ui()

    def setup_ui(self):
        """Configura os widgets da aba 'Cadastrar Usuário'."""
        self.tab.grid_columnconfigure(0, weight=1)
        self.tab.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self.tab)
        container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)

        # --- Formulário de Cadastro de Usuário ---
        form_frame = ctk.CTkFrame(container)
        form_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="Nome de Usuário:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.username_entry = ctk.CTkEntry(form_frame, width=250)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Senha:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.password_entry = ctk.CTkEntry(form_frame, width=250, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Função (Role):").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.role_menu = ctk.CTkOptionMenu(form_frame, values=["professor", "admin"])
        self.role_menu.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.role_menu.set("professor") # Valor padrão

        self.register_button = ctk.CTkButton(form_frame, text="Cadastrar Usuário", command=self.register_user)
        self.register_button.grid(row=3, column=0, columnspan=2, padx=10, pady=20)
        
        self.status_label = ctk.CTkLabel(form_frame, text="", font=ctk.CTkFont(size=14))
        self.status_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

    def register_user(self):
        """Cadastra um novo usuário no banco de dados."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_menu.get()

        if not username or not password:
            self.status_label.configure(text="Nome de usuário e senha são obrigatórios.", text_color="red")
            return

        try:
            new_user_id = db.add_user(username, password, role)
            if new_user_id:
                self.status_label.configure(text=f"Usuário '{username}' cadastrado com sucesso!", text_color="green")
                # Limpar campos após o sucesso
                self.username_entry.delete(0, 'end')
                self.password_entry.delete(0, 'end')
            else:
                self.status_label.configure(text="Nome de usuário já existe.", text_color="orange")
        except Exception as e:
            self.status_label.configure(text=f"Erro ao salvar no banco de dados: {e}", text_color="red")

