# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime, time, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = "presenca.db"

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Inicializa o banco de dados, criando as tabelas se elas não existirem.
    """
    # Conecta ao banco de dados (cria se não existir)
    conn = get_db_connection()
    cursor = conn.cursor()
    print("Verificando e inicializando tabelas do banco de dados...")

    # Verifica e cria a tabela 'alunos'
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alunos'")
    if cursor.fetchone() is None:
        print("Criando tabela 'alunos'...")
        cursor.execute("""
        CREATE TABLE alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ra TEXT UNIQUE NOT NULL,
            inep TEXT UNIQUE,
            nome TEXT NOT NULL,
            codigo_turma TEXT
        )""")

    # Verifica e cria a tabela 'presenca'
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='presenca'")
    if cursor.fetchone() is None:
        print("Criando tabela 'presenca'...")
        cursor.execute("""
        CREATE TABLE presenca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            tipo_registro TEXT NOT NULL, -- 'entrada' ou 'saida'
            FOREIGN KEY (aluno_id) REFERENCES alunos (id)
        )""")

    # Verifica e cria a tabela 'users'
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone() is None:
        print("Criando tabela 'users'...")
        cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )""")

    conn.commit()
    # Add a default admin user for initial setup
    # Check if the 'users' table is empty before adding the default user
    cursor.execute("SELECT COUNT(*) FROM users")
    # ATENÇÃO: O usuário 'admin' com senha 'admin' é criado por padrão.
    # Isso é uma falha de segurança e deve ser alterado em um ambiente de produção.
    if cursor.fetchone()[0] == 0:
        print("AVISO: Criando usuário padrão 'admin' com senha 'admin'. Altere esta senha assim que possível.")
        add_user("admin", "admin", "admin", conn) # Cria um usuário 'admin' com a role 'admin'
    conn.close()
    print("Verificação do banco de dados concluída.")

def add_user(username, password, role, conn=None):
    """Adiciona um novo usuário ao banco de dados."""
    if conn is None:
        conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None # Username já existe
    finally:
        if conn is not None and conn != get_db_connection(): # Only close if not passed in
            conn.close()

def get_user_by_username(username):
    """Busca um usuário pelo nome de usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    """Busca todos os usuários cadastrados no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users ORDER BY username")
    users = cursor.fetchall()
    conn.close()
    return [dict(row) for row in users]

def delete_user_by_id(user_id):
    """Deleta um usuário pelo seu ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def check_user_password(hashed_password, password):
    """Verifica se a senha fornecida corresponde à senha hash."""
    return check_password_hash(hashed_password, password)

def add_student(ra, nome, codigo_turma, inep=None):
    """Adiciona um novo aluno ao banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO alunos (ra, nome, codigo_turma, inep) VALUES (?, ?, ?, ?)",
            (ra, nome, codigo_turma, inep)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None # RA já existe
    finally:
        conn.close()

def get_student_by_ra(ra):
    """Busca um aluno pelo RA."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alunos WHERE ra = ?", (ra,))
    student = cursor.fetchone()
    conn.close()
    return dict(student) if student else None

def get_student_by_identifier(identifier):
    """Busca um aluno pelo RA ou pelo INEP."""
    conn = get_db_connection()
    # Tenta encontrar pelo RA primeiro, depois pelo INEP.
    student = conn.execute(
        'SELECT * FROM alunos WHERE ra = ? OR inep = ?', (identifier, identifier)
    ).fetchone()
    conn.close()
    return student

# --- Constantes de Horário ---
HORA_ENTRADA_PADRAO = time(7, 20)
HORA_SAIDA_PADRAO = time(16, 20)
TOLERANCIA_MINUTOS = timedelta(minutes=20)

def add_attendance_record(aluno_id):
    """
    Adiciona um registro de entrada ou saída para um aluno com base no horário.
    Retorna uma tupla (tipo_registro, status_detalhado).
    Ex: ('entrada', 'Entrada no horário') ou ('saida', 'Saída Antecipada')
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    agora = datetime.now()
    hora_atual = agora.time()
    hoje_inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)

    # Define as janelas de tempo
    inicio_janela_entrada = (datetime.combine(agora.date(), HORA_ENTRADA_PADRAO) - TOLERANCIA_MINUTOS).time()
    fim_janela_entrada = (datetime.combine(agora.date(), HORA_ENTRADA_PADRAO) + TOLERANCIA_MINUTOS).time()
    inicio_janela_saida = (datetime.combine(agora.date(), HORA_SAIDA_PADRAO) - TOLERANCIA_MINUTOS).time()
    
    tipo_registro = None
    status_detalhado = "Horário Inválido"

    # Lógica para determinar se é entrada ou saída
    if hora_atual < fim_janela_entrada:
        tipo_registro = 'entrada'
        status_detalhado = "Entrada no horário" if hora_atual <= fim_janela_entrada else "Entrada com Atraso"
    elif hora_atual >= inicio_janela_saida:
        tipo_registro = 'saida'
        status_detalhado = "Saída no horário" if hora_atual >= inicio_janela_saida else "Saída Antecipada"

    if tipo_registro:
        # Deleta registros anteriores do mesmo tipo no mesmo dia para garantir apenas o último
        cursor.execute(
            "DELETE FROM presenca WHERE aluno_id = ? AND tipo_registro = ? AND timestamp >= ?",
            (aluno_id, tipo_registro, hoje_inicio_dia)
        )
        # Insere o novo registro
        cursor.execute(
            "INSERT INTO presenca (aluno_id, tipo_registro, timestamp) VALUES (?, ?, ?)",
            (aluno_id, tipo_registro, agora)
        )
        conn.commit()

    conn.close()
    return tipo_registro, status_detalhado

def get_all_students_with_latest_attendance():
    """
    Busca todos os alunos e calcula o status de presença com base nos registros de entrada e saída do dia.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Define os horários de referência para a consulta SQL
    fim_entrada_tolerancia = (datetime.combine(datetime.today(), HORA_ENTRADA_PADRAO) + TOLERANCIA_MINUTOS).time().strftime('%H:%M:%S')
    inicio_saida_tolerancia = (datetime.combine(datetime.today(), HORA_SAIDA_PADRAO) - TOLERANCIA_MINUTOS).time().strftime('%H:%M:%S')

    query = f"""
    SELECT
        a.ra,
        a.nome,
        a.codigo_turma,
        CASE
            -- Se há registro de entrada, o aluno não está mais ausente.
            WHEN entrada.id IS NOT NULL AND saida.id IS NULL THEN 'Apenas Entrada'
            -- Saída antecipada
            WHEN entrada.id IS NOT NULL AND saida.id IS NOT NULL AND TIME(saida.timestamp) < '{inicio_saida_tolerancia}' THEN 'Saída Antecipada'
            -- Chegou atrasado, mas saiu no horário
            WHEN entrada.id IS NOT NULL AND saida.id IS NOT NULL AND TIME(entrada.timestamp) > '{fim_entrada_tolerancia}' THEN 'Atraso'
            -- Cenário ideal: Entrada e Saída corretas
            WHEN entrada.id IS NOT NULL AND saida.id IS NOT NULL THEN 'Presente'
            ELSE 'Ausente'
        END as status_presenca,
        entrada.timestamp as timestamp_entrada,
        saida.timestamp as timestamp_saida
    FROM
        alunos a
    LEFT JOIN (
        SELECT aluno_id, id, MAX(timestamp) as timestamp FROM presenca
        WHERE tipo_registro = 'entrada' AND DATE(timestamp) = DATE('now', 'localtime')
        GROUP BY aluno_id
    ) entrada ON a.id = entrada.aluno_id
    LEFT JOIN (
        SELECT aluno_id, id, MAX(timestamp) as timestamp FROM presenca
        WHERE tipo_registro = 'saida' AND DATE(timestamp) = DATE('now', 'localtime')
        GROUP BY aluno_id
    ) saida ON a.id = saida.aluno_id
    ORDER BY
        a.nome;
    """

    cursor.execute(
        query
    )
    students = cursor.fetchall()
    conn.close()
    student_list = [dict(row) for row in students]
    return student_list


def get_student_attendance_history_by_id(aluno_id):
    """Busca o histórico de presença de um aluno pelo seu ID interno."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, tipo_registro FROM presenca WHERE aluno_id = ? ORDER BY timestamp DESC",
        (aluno_id,)
    )
    history = cursor.fetchall()
    conn.close()
    return [dict(row) for row in history]

def get_student_attendance_history_by_ra(ra):
    """Busca o histórico de presença de um aluno pelo seu RA."""
    student = get_student_by_ra(ra)
    if not student:
        return None, None
    history = get_student_attendance_history_by_id(student['id'])
    return dict(student), [dict(h) for h in history]


def update_student_class(ra, codigo_turma):
    """Atualiza a turma de um aluno."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alunos SET codigo_turma = ? WHERE ra = ?",
        (codigo_turma, ra)
    )
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()
    return updated_rows > 0
    
def update_student(ra, data_dict):
    """
    Atualiza os dados de um aluno de forma genérica.
    'data_dict' é um dicionário com as colunas a serem atualizadas.
    Ex: {'codigo_turma': 'nova_turma', 'inep': '123'}
    """
    if not data_dict:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    
    set_clause = ", ".join([f"{key} = ?" for key in data_dict.keys()])
    values = list(data_dict.values())
    values.append(ra)

    query = f"UPDATE alunos SET {set_clause} WHERE ra = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    updated_rows = cursor.rowcount
    conn.close()
    return updated_rows > 0

if __name__ == '__main__':
    init_db()
