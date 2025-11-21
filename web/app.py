# -*- coding: utf-8 -*-
import os
from functools import wraps
import json
from flask import Flask, render_template, abort, jsonify, request, session, redirect, url_for, flash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import database as db

# ==============================================================================
# --- CONFIGURAÇÃO INICIAL DA APLICAÇÃO FLASK ---
# ==============================================================================

# Cria uma instância da aplicação Flask.
app = Flask(
    __name__,
    template_folder='templates'  # Garante que o Flask procure templates na pasta 'web/templates'
)

# Define a chave secreta. É crucial para a segurança da sessão.
# Em um ambiente de produção, use uma variável de ambiente para maior segurança.
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey-for-dev')

# Carrega os nomes das turmas para um cache em memória ao iniciar.
CLASS_NAMES = {}
try:
    # Constrói o caminho para o arquivo JSON de forma robusta
    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'turmas-com-disciplinas.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        turmas_data = json.load(f)
        # Cria um dicionário mapeando codigoTurma -> nomeTurma
        CLASS_NAMES = {item['codigoTurma']: item['nomeTurma'] for item in turmas_data}
    print("Nomes das turmas carregados com sucesso.")
except Exception as e:
    print(f"AVISO: Não foi possível carregar os nomes das turmas do arquivo JSON. Erro: {e}")


# Cria um serializador para gerar tokens seguros com tempo de expiração.
token_serializer = URLSafeTimedSerializer(app.secret_key)


# ==============================================================================
# --- DECORATORS DE AUTENTICAÇÃO E AUTORIZAÇÃO ---
# ==============================================================================

def login_required(f):
    """
    Decorator que garante que o usuário esteja logado para acessar uma rota.
    Se não estiver logado, redireciona para a página de login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def professor_or_admin_required(f):
    """
    Decorator que garante que o usuário tenha a função 'professor' ou 'admin'
    para acessar uma rota.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') not in ['professor', 'admin']:
            flash('Você não tem permissão para acessar esta funcionalidade.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator que garante que o usuário tenha a função 'admin' para acessar uma rota.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# --- ROTAS DE AUTENTICAÇÃO (LOGIN/LOGOUT) ---
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Renderiza a página de login e processa o formulário de login.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.get_user_by_username(username)

        if user and db.check_user_password(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/login-with-token')
def login_with_token():
    """
    Endpoint para fazer login usando um token seguro (geralmente de um QR code).
    O token é validado (assinatura e tempo de expiração de 1 minuto).
    """
    token = request.args.get('token')
    if not token:
        flash('Token de login ausente.', 'danger')
        return redirect(url_for('login'))

    try:
        # Valida o token com um tempo de expiração de 60 segundos.
        ra = token_serializer.loads(token, max_age=60)
        user = db.get_user_by_username(ra)
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login via QR Code realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário do token não encontrado.', 'danger')
            return redirect(url_for('login'))
    except SignatureExpired:
        flash('O token de login expirou. Por favor, tente novamente.', 'danger')
        return redirect(url_for('login'))
    except BadTimeSignature:
        flash('Token de login inválido.', 'danger')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Ocorreu um erro durante o login com token: {e}', 'danger')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """
    Remove os dados do usuário da sessão, efetivamente fazendo o logout.
    """
    session.pop('username', None)
    session.pop('role', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))


# ==============================================================================
# --- ROTAS PRINCIPAIS DA APLICAÇÃO ---
# ==============================================================================

@app.route('/')
def index():
    """
    Renderiza a página inicial da aplicação web (o dashboard de presença).
    Esta rota agora lida com todos os contextos de usuário.
    """
    # Se não há usuário na sessão, ele é um visitante não autenticado.
    if 'username' not in session:
        return render_template('visitante_home.html')
    user_role = session.get('role')

    if user_role == 'aluno': # Contexto: Aluno
        # Alunos têm uma visão completamente separada e simplificada.
        api_base_url = f"http://{request.host.split(':')[0]}:5000"
        return render_template('aluno_view.html', user_role=user_role, api_base_url=api_base_url)

    # Contexto: Professor, Admin ou Visitante autenticado
    # Define se dados sensíveis (como RA) podem ser vistos.
    # O visitante autenticado verá o dashboard, mas sem dados sensíveis.
    api_base_url = f"http://{request.host.split(':')[0]}:5000"
    can_view_sensitive_data = user_role in ['professor', 'admin']

    return render_template('index.html', user_role=user_role, can_view_sensitive_data=can_view_sensitive_data, api_base_url=api_base_url)

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    """
    Página para administradores gerenciarem usuários (listar, adicionar, excluir).
    """
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            if username and password and role:
                if db.add_user(username, password, role):
                    flash(f'Usuário "{username}" adicionado com sucesso!', 'success')
                else:
                    flash(f'Usuário "{username}" já existe.', 'warning')
            else:
                flash('Todos os campos são obrigatórios para adicionar um usuário.', 'danger')

        elif action == 'delete':
            user_id = request.form.get('user_id')
            # Impede que o admin se auto-delete
            if str(session.get('user_id')) == str(user_id):
                 flash('Você não pode excluir sua própria conta de administrador.', 'danger')
            elif db.delete_user_by_id(user_id):
                flash('Usuário excluído com sucesso!', 'success')

        return redirect(url_for('manage_users'))

    users = db.get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/aluno/<ra>')
@login_required
def student_history(ra):
    """
    Renderiza a página com o histórico de presença de um aluno específico.
    """
    try:
        aluno, historico = db.get_student_attendance_history_by_ra(ra)
        if not aluno:
            abort(404)  # Aluno não encontrado
    except Exception as e:
        print(f"Erro ao buscar histórico do aluno {ra}: {e}")
        abort(500)  # Erro interno do servidor

    return render_template('historico.html', aluno=aluno, historico=historico)


# ==============================================================================
# --- ENDPOINTS DE API (PARA COMUNICAÇÃO COM O FRONTEND) ---
# ==============================================================================

@app.route('/api/generate-login-token', methods=['POST'])
def generate_login_token():
    """
    Gera um token de login para um usuário se ele for um professor.
    Usado pela aplicação desktop para permitir o login via QR code.
    """
    data = request.get_json()
    if not data or 'ra' not in data:
        return jsonify({"error": "RA do usuário não fornecido."}), 400

    ra = data['ra']
    user = db.get_user_by_username(ra)

    if user and user['role'] == 'professor':
        # Gera um token que expira em 1 minuto.
        token = token_serializer.dumps(ra)
        return jsonify({"token": token, "role": "professor", "nome": user['username']})
    elif user:
        # Se for um usuário, mas não professor, informa o role.
        return jsonify({"role": "aluno", "nome": user['username']})
    else:
        # Se não for um usuário, verifica se é um aluno para dar a presença.
        student = db.get_student_by_ra(ra)
        if student:
            return jsonify({"role": "aluno", "nome": student['nome']})
        else:
            return jsonify({"error": "Usuário ou aluno não encontrado."}), 404

@app.route('/api/presence_data', methods=['GET'])
def get_presence_data():
    """
    Retorna todos os dados de presença dos alunos em formato JSON.
    Se o usuário logado for um aluno, retorna apenas os seus próprios dados.
    """
    try:
        all_students = db.get_all_students_with_latest_attendance()
        
        # Adiciona o nome da turma a cada registro de aluno
        for student in all_students:
            # Usa o nome da turma do cache ou o próprio código se não for encontrado
            student['nome_turma'] = CLASS_NAMES.get(student['codigo_turma'], student['codigo_turma'])

        students_to_return = all_students
        user_role = session.get('role')
        if user_role == 'aluno':
            logged_in_ra = session.get('username')
            students_to_return = [aluno for aluno in students_to_return if aluno['ra'] == logged_in_ra]
            
        return jsonify(students_to_return)
    except Exception as e:        
        print(f"[ERRO-API] Erro ao buscar dados de presença para API: {e}")
        return jsonify({"error": "Erro ao buscar dados de presença"}), 500

@app.route('/api/repopulate_students', methods=['POST'])
@login_required
@professor_or_admin_required
def repopulate_students():
    """
    Endpoint para forçar a limpeza e repopulação do banco de dados de alunos.
    Acessível apenas por usuários com a função 'professor'.
    """
    try:
        count, errors = db.repopulate_all_students()
        if errors:
            return jsonify({
                "message": f"{count} alunos importados, mas ocorreram {len(errors)} erros.",
                "errors": errors
            }), 400
        return jsonify({
            "message": f"Banco de dados repopulado com sucesso! {count} alunos importados."
        }), 200
    except Exception as e:
        return jsonify({"error": f"Ocorreu um erro grave: {e}"}), 500


# ==============================================================================
# --- FUNÇÃO DE INICIALIZAÇÃO DO SERVIDOR ---
# ==============================================================================

def start_web_server():
    """
    Inicia o servidor Flask.
    """
    print("Iniciando o servidor web em http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    # Bloco para permitir a execução deste arquivo de forma independente para testes.
    # sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    init_db()
    # populate_students_if_empty()
    
    # Em modo de teste, ativamos o debug.
    app.run(host='0.0.0.0', port=5000, debug=True)
