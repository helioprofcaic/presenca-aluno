# Guia de Solução de Problemas (Troubleshooting)

Este documento aborda os erros mais comuns que podem ocorrer ao configurar ou executar o Sistema de Registro de Presença.

## 1. Erro: `FileNotFoundError` ao importar `pyzbar`

Este é o problema mais comum no Windows.

### Sintomas

Ao executar `python main.py`, a aplicação falha imediatamente com um dos seguintes erros:

```
Traceback (most recent call last):
  ...\nFileNotFoundError: Could not find module 'libiconv.dll' (or one of its dependencies).
```

ou

```
Traceback (most recent call last):
  ...\nFileNotFoundError: Could not find module 'D:\\...\\Lib\\site-packages\\pyzbar\\libzbar-64.dll' (or one of its dependencies).
```

### Causa

A biblioteca `pyzbar` é uma interface para a biblioteca ZBar, que é escrita em C. O erro significa que o Python não conseguiu encontrar os arquivos `.dll` da ZBar (como `libzbar-64.dll` e suas dependências, como `libiconv.dll`). Isso acontece porque a instalação do `pyzbar` via `pip` não inclui ou não configura o caminho para essas bibliotecas no Windows.

### Solução

A solução é instalar a biblioteca ZBar manualmente e adicionar sua localização à variável de ambiente `PATH` do Windows.

1.  **Baixe e Instale o ZBar:**
    *   Faça o download do instalador `zbar-0.10-setup.exe` [neste link do SourceForge](https://sourceforge.net/projects/zbar/files/zbar/0.10/zbar-0.10-setup.exe/download).
    *   Execute o instalador. O caminho de instalação padrão é `C:\Program Files (x86)\ZBar`.

2.  **Adicione a Pasta `bin` ao PATH:**
    *   Abra o menu "Editar as variáveis de ambiente do sistema".
    *   Clique em "Variáveis de Ambiente...".
    *   Na seção "Variáveis do sistema", selecione `Path` e clique em "Editar...".
    *   Clique em "Novo" e adicione o caminho para a pasta `bin` do ZBar: `C:\Program Files (x86)\ZBar\bin`.
    *   Confirme as alterações clicando em "OK".

3.  **Reinicie seu Ambiente:**
    *   **É crucial fechar e reabrir seu terminal, VS Code ou qualquer outro ambiente** onde você está executando o comando `python`. O sistema só carrega as novas variáveis de ambiente em processos recém-iniciados.

## 2. Problema: A aplicação trava, pisca ou não fecha

### Sintomas

- A janela da aplicação fica branca ou preta.
- A imagem da webcam congela.
- A janela não responde a cliques e não pode ser fechada pelo botão "X".
- O terminal pode exibir a mensagem "Está piscando, travando e não quer fechar" ou similar, se houver `prints` de depuração.

### Causa

Este problema ocorre quando uma tarefa de longa duração (como ler um feed de vídeo em um loop `while True`) é executada na *thread principal* da interface gráfica (GUI). A thread principal é responsável por desenhar a janela, responder a cliques e manter a aplicação fluida. Se ela estiver ocupada processando o vídeo, não consegue fazer mais nada, e a aplicação "congela".

### Solução

A solução é mover o processamento de vídeo para uma *thread secundária*, deixando a thread principal livre para gerenciar a interface.

O código em `main.py` já implementa esta solução:
- A função `video_stream_worker` contém o loop de captura de vídeo e é executada em uma `threading.Thread` separada.
- Uma `queue.Queue` é usada para comunicar de forma segura os frames de vídeo da thread secundária para a thread principal.
- A função `update_gui` (executada na thread principal) apenas busca o frame mais recente da fila e o exibe, sem bloquear a interface.

Se você encontrar esse problema em outro projeto, a solução é refatorar o código para seguir um padrão semelhante de multithreading.

## 3. Aviso: `CTkLabel Warning: Given image is not CTkImage`

### Sintomas

Um aviso aparece no terminal durante a execução:

```
UserWarning: CTkLabel Warning: Given image is not CTkImage but <class 'PIL.ImageTk.PhotoImage'>. Image can not be scaled on HighDPI displays, use CTkImage instead.
```

### Causa

O CustomTkinter possui seu próprio objeto de imagem, `CTkImage`, que é otimizado para o framework, especialmente para o correto dimensionamento em telas com alta densidade de pixels (HighDPI). O aviso informa que você está usando um objeto de imagem do `PIL` (`PhotoImage`) diretamente, o que pode resultar em imagens com tamanho incorreto em algumas telas.

### Solução

A solução é encapsular a imagem do `PIL` dentro de um objeto `CTkImage` antes de passá-la para um widget do CustomTkinter.

O código em `main.py` já faz isso corretamente:

```python
# Converte a imagem do OpenCV para o formato do PIL
cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
img = Image.fromarray(cv2image)

# Cria um objeto CTkImage a partir da imagem do PIL
ctk_img = ctk.CTkImage(light_image=img, size=(width, height))

# Usa o objeto CTkImage no widget
self.video_label.configure(image=ctk_img)
```