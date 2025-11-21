import database as db
import qrcode
import argparse
from PIL import Image
import os

def create_user_and_generate_qr(username, password, role="aluno"):
    """
    Cria um usuário no banco de dados e gera um QR Code com o username.
    """
    print(f"Tentando adicionar usuário '{username}' com a role '{role}'...")
    user_id = db.add_user(username, password, role)
    if user_id:
        print(f"Usuário '{username}' ({role}) adicionado com sucesso ao banco de dados com ID: {user_id}.")
    else:
        print(f"Aviso: Usuário '{username}' já existe ou houve um problema ao adicionar.")

    # Gerar QR Code
    qr_data = username # O QR code conterá o nome de usuário (RA)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Define o caminho para salvar o QR code
    qrcodes_dir = "qrcodes"
    os.makedirs(qrcodes_dir, exist_ok=True)
    qr_filename = os.path.join(qrcodes_dir, f"user_{username}.png")
    img.save(qr_filename)

    print(f"QR Code para o RA '{username}' gerado e salvo em: {qr_filename}")
    print("\n--- Informações de Login e Uso ---")
    print(f"Para fazer login na aplicação web (http://localhost:5000/login), use:")
    print(f"  Usuário: {username}")
    print(f"  Senha: {password}")
    print(f"\nO QR Code gerado ('{qr_filename}') pode ser usado para registrar presença na aplicação desktop (aba 'Ler QR Code').")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cria um novo usuário e seu QR Code correspondente.")
    parser.add_argument("username", help="Nome de usuário (ex: 'visitante', 'professor_joao', ou o RA de um aluno).")
    parser.add_argument("password", help="Senha para o novo usuário.")
    parser.add_argument("role", choices=["aluno", "professor", "admin", "visitante"], help="O perfil do usuário.")

    args = parser.parse_args()

    # Garante que o banco de dados esteja inicializado
    db.init_db()
    
    create_user_and_generate_qr(args.username, args.password, role=args.role)

    print("\nExemplo de uso:")
    print("python create_user_and_qr.py visitante visitante visitante")
    print("python create_user_and_qr.py prof_ana senha123 professor")
    print("python create_user_and_qr.py 12345678 12345678 aluno")
