# Guia de Build e Release

Este guia detalha o processo de "buildar" o projeto, ou seja, empacotá-lo em um executável (`.exe` para Windows) que pode ser distribuído e executado em outros computadores sem a necessidade de instalar Python ou qualquer dependência.

## 1. Pré-requisitos

A ferramenta principal que usaremos é o **PyInstaller**.

- **Instale o PyInstaller:**
  Certifique-se de que seu ambiente virtual esteja ativado e execute o comando:
  ```bash
  pip install pyinstaller
  ```

## 2. Criando o Executável (`.exe`)

O processo de build é feito através de um único comando no terminal, executado a partir da pasta raiz do projeto (`presenca-aluno/`).

### Passo 1: O Comando de Build

Abra seu terminal na raiz do projeto e execute o seguinte comando:

```bash
pyinstaller --name PresencaAluno --onefile --windowed --add-data "data;data" --add-data "web;web" run.py
```

### Passo 2: Entendendo o Comando

Vamos analisar cada parte do comando para entender o que ela faz:

- `pyinstaller`: Invoca a ferramenta de build.
- `--name PresencaAluno`: Define o nome do arquivo executável final. O resultado será `PresencaAluno.exe`.
- `--onefile`: Agrupa todos os arquivos necessários (código, dependências, etc.) em um único arquivo `.exe`. Isso facilita a distribuição, mas pode fazer com que a aplicação demore um pouco mais para iniciar.
- `--windowed`: Impede que uma janela de console (terminal preto) seja aberta junto com a sua aplicação gráfica. Essencial para aplicações com interface.
- `--add-data "origem;destino"`: Esta é a parte mais crucial. O PyInstaller automaticamente encontra os arquivos de código Python, mas não sabe sobre outros arquivos que seu programa precisa, como a pasta `web` (com os templates e arquivos estáticos) e a pasta `data` (com os JSONs dos alunos).
  - `--add-data "data;data"`: Inclui a pasta `data` e todo o seu conteúdo no pacote final.
  - `--add-data "web;web"`: Inclui a pasta `web` e todo o seu conteúdo no pacote final.
- `run.py`: Especifica o ponto de entrada da sua aplicação. O PyInstaller começará a análise a partir deste arquivo.

### Passo 3: Encontrando e Testando o Executável

Após a execução do comando, o PyInstaller criará algumas pastas. O seu executável final estará na pasta `dist/`:

`d:\Local\Dev\presenca-aluno\dist\PresencaAluno.exe`

**Teste Crucial:** Antes de distribuir, copie o arquivo `PresencaAluno.exe` para um local fora da pasta do projeto (por exemplo, sua Área de Trabalho) e execute-o. Verifique se tanto a aplicação desktop quanto a interface web (`http://localhost:5000`) funcionam corretamente. Isso simula o ambiente de um usuário final.

## 3. Criando um Pacote de Lançamento (Release)

Para facilitar o download, é uma boa prática compactar o executável em um arquivo `.zip` e publicá-lo na seção "Releases" do seu repositório no GitHub.

1.  Crie um arquivo `.zip` contendo o `PresencaAluno.exe`.
2.  No GitHub, vá para a página do seu repositório e clique em **"Releases"** > **"Draft a new release"**.
3.  Preencha as informações da versão (ex: `v1.0`), anexe o arquivo `.zip` e publique.