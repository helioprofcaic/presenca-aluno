# Guia de Desenvolvimento

Este documento fornece informações técnicas para desenvolvedores que desejam entender, modificar ou contribuir com o projeto.

## 1. Estrutura do Projeto

A estrutura de pastas e arquivos mais importante dentro de `presenca-aluno/` é:

```
presenca-aluno/
│
├── .venv/                   # Ambiente virtual do Python
├── data/                    # Arquivos .json para importação de alunos
│   ├── 294815.json
│   └── turmas-com-disciplinas.json
├── docs/                    # Documentação do projeto
│   ├── Como_usar.md
│   ├── Desenvolvimento.md
│   ├── Funcionalidades.md
│   └── TROUBLESHOOTING.md
├── qrcodes/                 # Onde os QR Codes gerados são salvos
│   └── turma_294815_ra_12345.png
│
├── web/                     # Aplicação web (Flask)
│   ├── static/              # Arquivos estáticos (CSS, JS, imagens)
│   └── templates/           # Templates HTML (Jinja2)
│   └── app.py               # Ponto de entrada da aplicação web
├── desktop/                 # Aplicação desktop (CustomTkinter)
│   └── main.py              # Ponto de entrada da aplicação desktop
├── database.py              # Módulo de interação com o banco de dados SQLite
├── presenca.db              # Banco de dados SQLite
├── run.py                   # Ponto de entrada principal (inicia desktop e web)
├── requirements.txt         # Lista de dependências Python
└── alunos.csv               # Arquivo CSV legado, não mais utilizado como banco de dados.
```

- **`run.py`**: O ponto de entrada principal que orquestra o início tanto da aplicação desktop quanto do servidor web Flask em threads separadas.
- **`desktop/main.py`**: O coração da aplicação desktop. Contém a classe `App` que gerencia a interface gráfica (usando CustomTkinter), a captura de vídeo (OpenCV), a decodificação de QR Code (pyzbar) e a lógica de negócios.
- **`web/app.py`**: O ponto de entrada da aplicação web. Define as rotas Flask, renderiza templates e interage com o banco de dados através de `database.py`.
- **`database.py`**: Módulo responsável por todas as operações de banco de dados (criação de tabelas, inserção, consulta, atualização) utilizando SQLite.
- **`presenca.db`**: O arquivo do banco de dados SQLite que armazena todas as informações de alunos, turmas e registros de presença.
- **`alunos.csv`**: Um arquivo CSV simples que atuava como banco de dados na versão anterior, armazenando o ID, nome, status de presença e código da turma de cada aluno. **Agora, o banco de dados principal é `presenca.db`.**
- **`data/`**: Diretório padrão para importar dados. A função de importação lê os arquivos `.json` desta pasta.
- **`qrcodes/`**: Diretório padrão onde os QR Codes gerados pela função de importação são salvos.

## 2. Configuração do Ambiente de Desenvolvimento

1.  **Clone o Repositório**:
    ```bash
    git clone <url-do-repositorio>
    cd presenca-aluno
    ```

2.  **Crie e Ative o Ambiente Virtual**:
    - No Windows:
      ```bash
      python -m venv .venv
      .venv\Scripts\activate
      ```
    - No Linux/macOS:
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      ```

3.  **Instale as Dependências**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Resolva o Problema do `pyzbar` (Windows)**:
    - A instalação do `pyzbar` no Windows requer uma etapa manual. Siga o guia em **[Solução de Problemas](./TROUBLESHOOTING.md)** para instalar a biblioteca ZBar e adicioná-la ao PATH do sistema.

5.  **Execute a Aplicação (Desktop e Web)**:
    ```bash
    python run.py
    ```
    Isso iniciará tanto a aplicação desktop quanto o servidor web Flask. O servidor web estará acessível em `http://0.0.0.0:5000` (ou `http://localhost:5000`).

## 3. Arquitetura do Código

O projeto agora consiste em duas aplicações (desktop e web) gerenciadas por um ponto de entrada principal (`run.py`), ambas interagindo com um banco de dados SQLite (`presenca.db`) através do módulo `database.py`.

### 3.1. Aplicação Desktop (`desktop/main.py`)

O código está centralizado na classe `App`, que herda de `customtkinter.CTk`.

- **`__init__(self)`**:
    - Configura a janela principal e o layout de abas.
    - Chama os métodos `setup_*_tab()` para construir a interface de cada aba.
    - Inicializa variáveis de controle (ex: `last_qr_time`) e o gerenciador da câmera (`cap`, `running`, `queue`).
    - Associa o evento de fechamento da janela (`on_closing`) e a troca de abas (`on_tab_change`).

- **`setup_*_tab(self)`**:
    - Cada método é responsável por criar e posicionar os widgets (botões, labels, etc.) de uma aba específica.

- **`on_tab_change(self)`**:
    - Um *callback* que é executado sempre que o usuário troca de aba.
    - Sua principal função é iniciar a captura de vídeo (`start_video()`) apenas quando a aba "Ler QR Code" é selecionada e pará-la (`stop_video()`) em qualquer outra aba, economizando recursos.

- **Lógica da Câmera (Multithreading)**:
    - Para evitar que a interface congele, a captura de vídeo é feita em uma *thread* separada.
    - **`start_video()`**: Cria e inicia a `threading.Thread` que executará `video_stream_worker`.
    - **`video_stream_worker()`**: É um loop `while self.running` que continuamente lê frames da câmera usando `cv2`. Os frames são colocados em uma `queue.Queue` para serem processados pela thread principal.
    - **`update_gui()`**: Executada na thread principal, esta função é chamada repetidamente com `self.after()`. Ela tenta pegar um frame da fila (sem bloquear), exibe-o na tela e processa qualquer QR Code detectado.
    - **`stop_video()`**: Para a thread de vídeo e libera a câmera.

- **Manipulação de Dados (Desktop)**:
    - As funções de manipulação de dados no desktop (ex: `update_presence()`, `register_student()`, `import_students_from_json()`) agora interagem com o `database.py` para persistir e recuperar informações do `presenca.db`.

### 3.2. Aplicação Web (`web/app.py`)

A aplicação web é construída com Flask e serve como uma interface alternativa para visualizar e gerenciar os dados de presença.

- **Rotas Principais**:
    - **`/`**: Renderiza a página inicial (`index.html`) que exibe o status de presença dos alunos, agrupados por turma, com funcionalidades de filtro, impressão e exportação.
    - **`/aluno/<ra>`**: Renderiza a página de histórico de presença para um aluno específico (`historico.html`).
- **APIs (JSON)**:
    - **`/api/presence_data` (GET)**: Retorna todos os dados de presença dos alunos em formato JSON, utilizados pelo frontend JavaScript para renderização dinâmica.
    - **`/api/save_presence` (POST)**: Um endpoint placeholder para futuras funcionalidades de salvar dados de presença (ex: atualizações feitas na interface web).
- **Interação com o Banco de Dados**:
    - A aplicação web utiliza o módulo `database.py` para todas as operações de leitura e escrita no `presenca.db`.

### 3.3. Módulo de Banco de Dados (`database.py`)

Este módulo centraliza toda a lógica de interação com o banco de dados SQLite (`presenca.db`).

- **`init_db()`**: Garante que o banco de dados e as tabelas necessárias (`alunos`, `presencas`, etc.) sejam criados se ainda não existirem.
- **Funções CRUD**: Contém funções para Criar, Ler, Atualizar e Deletar (CRUD) registros de alunos e presenças.

## 4. Principais Bibliotecas Utilizadas

- **`customtkinter`**: Para a criação da interface gráfica moderna da aplicação desktop.
- **`opencv-python` (`cv2`)**: Para acessar a webcam e capturar o vídeo na aplicação desktop.
- **`pyzbar`**: Para decodificar os dados contidos nos QR Codes na aplicação desktop.
- **`pandas`**: Para manipulação de dados, especialmente para leitura e escrita de CSVs (legado) e para auxiliar na manipulação de dados em memória.
- **`qrcode`**: Para gerar as imagens de QR Code para os alunos na aplicação desktop.
- **`Pillow` (`PIL`)**: Para manipular imagens, principalmente para converter os formatos entre OpenCV, qrcode e CustomTkinter.
- **`threading`** e **`queue`**: Para garantir que a interface do usuário da aplicação desktop permaneça responsiva durante a captura de vídeo.
- **`Flask`**: O microframework web utilizado para construir a aplicação web.
- **`sqlite3`**: Módulo padrão do Python para interagir com bancos de dados SQLite (utilizado indiretamente via `database.py`).
