# -*- coding: utf-8 -*-
"""
Ponto de entrada principal para a aplicação do Sistema de Presença.

Este script é responsável por iniciar e executar a aplicação desktop (CustomTkinter)
e o servidor web (Flask) simultaneamente, permitindo uma experiência integrada
para a feira de profissões.
"""

import threading
import os
import sys
import json
from pathlib import Path
import database as db # Importa o módulo de banco de dados

# Adiciona o diretório do projeto ao sys.path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)

try:
    from desktop.main import start_desktop_app
    from web.app import start_web_server
    from database import init_db
except ImportError as e:
    print(f"Erro de importação: {e}")
    sys.exit(1)

def populate_students_if_empty():
    """
    Verifica se a tabela de alunos está vazia e, se estiver, popula-a
    a partir dos arquivos JSON na pasta 'data'.
    """
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alunos")
    student_count = cursor.fetchone()[0]
    conn.close()

    if student_count > 0:
        print(f"Banco de dados já contém {student_count} alunos. Nenhum aluno importado.")
        return

    print("Tabela 'alunos' está vazia. Iniciando importação a partir de arquivos JSON...")
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("Erro: Pasta 'data' não encontrada. Não é possível importar alunos.")
        return

    imported_count = 0
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
                inep = str(student_data.get('inep')) if student_data.get('inep') else None

                if not nome or not ra:
                    errors.append(f"Dados incompletos no arquivo {json_file.name}")
                    continue
                
                # Adiciona o aluno à tabela 'alunos'
                student_id = db.add_student(ra, nome, codigo_turma_from_file, inep=inep)
                # Cria também um usuário para o aluno poder logar, com o RA como senha padrão
                db.add_user(ra, ra, "aluno")
                imported_count += 1

        except json.JSONDecodeError:
            errors.append(f"Erro de JSON em {json_file.name}.")
        except Exception as e:
            errors.append(f"Erro ao processar {json_file.name}: {e}")
    
    if errors:
        print(f"Importação concluída com {len(errors)} erros.")
        for err in errors:
            print(f" - {err}")
    
    print(f"Importação concluída. {imported_count} alunos foram adicionados ao banco de dados.")


def run_web_server():
    """Função alvo para a thread do servidor web."""
    print("Iniciando a thread do servidor web...")
    start_web_server()

def run_desktop_app():
    """Função alvo para a thread principal da aplicação desktop."""
    print("Iniciando a aplicação desktop na thread principal...")
    start_desktop_app()

if __name__ == "__main__":
    print("Lançador principal iniciado.")
    
    # Inicializa o banco de dados (cria tabelas se não existirem)
    init_db()
    
    # Popula o banco de dados com alunos se estiver vazio
    populate_students_if_empty()
    
    # Configura e inicia o servidor web em uma thread separada
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Inicia a aplicação desktop na thread principal
    run_desktop_app()
    
    print("Aplicação desktop encerrada. O programa principal foi finalizado.")
