# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime
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
            status TEXT NOT NULL,
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

def add_student(ra, nome, codigo_turma):
    """Adiciona um novo aluno ao banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO alunos (ra, nome, codigo_turma) VALUES (?, ?, ?)",
            (ra, nome, codigo_turma)
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
    return student

def add_attendance_record(aluno_id, status):
    """Adiciona um registro de presença para um aluno."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO presenca (aluno_id, status, timestamp) VALUES (?, ?, ?)",
        (aluno_id, status, datetime.now())
    )
    conn.commit()
    conn.close()

def get_all_students_with_latest_attendance():
    """
    Busca todos os alunos e o status da última presença registrada para cada um.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    WITH LatestPresence AS (
        SELECT
            aluno_id,
            status,
            timestamp,
            ROW_NUMBER() OVER(PARTITION BY aluno_id ORDER BY timestamp DESC) as rn
        FROM presenca
    )
    SELECT
        a.ra,
        a.nome,
        a.codigo_turma,
        COALESCE(lp.status, 'Ausente') as status_presenca,
        lp.timestamp
    FROM
        alunos a
    LEFT JOIN
        LatestPresence lp ON a.id = lp.aluno_id AND lp.rn = 1
    ORDER BY
        a.nome;
    """

    cursor.execute(query)
    students = cursor.fetchall()
    conn.close()
    student_list = [dict(row) for row in students]
    print(f"[DEBUG-DB] get_all_students_with_latest_attendance: Encontrados {len(student_list)} registros de alunos.")
    return student_list


def get_student_attendance_history_by_id(aluno_id):
    """Busca o histórico de presença de um aluno pelo seu ID interno."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, status FROM presenca WHERE aluno_id = ? ORDER BY timestamp DESC",
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
    return student, history


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

if __name__ == '__main__':
    init_db()
