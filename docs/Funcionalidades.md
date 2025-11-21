# Funcionalidades do Sistema

Este documento descreve em detalhes cada uma das funcionalidades disponíveis na aplicação, organizadas pelas abas da interface.

## Aba: Apresentação

A primeira tela ao abrir o aplicativo.

- **Boas-vindas**: Exibe uma mensagem de boas-vindas e uma breve introdução ao sistema.
- **Navegação**: Orienta o usuário sobre as funcionalidades das outras abas.
- **Acesso à Versão Web**: Apresenta um QR Code que, ao ser escaneado, leva o usuário para a versão web da aplicação (se disponível).

## Aba: Ler QR Code

O coração do sistema, onde a mágica do registro de presença acontece.

- **Visualização da Câmera**: Ativa a webcam do computador e exibe a imagem em tempo real.
- **Detecção de QR Code**: Identifica e decodifica automaticamente qualquer QR Code apresentado à câmera. Um retângulo verde é desenhado ao redor do QR Code detectado.
- **Registro de Presença**:
    - Ao ler um QR Code válido correspondente a um aluno, o sistema atualiza o status desse aluno para "Presente" no arquivo `alunos.csv`.
    - **Feedback Visual**: Uma mensagem na tela confirma a presença do aluno, exibindo seu nome e uma cor verde.
    - **Aluno Não Encontrado**: Se o QR Code não corresponder a nenhum aluno cadastrado, uma mensagem de erro é exibida em vermelho.
- **Cooldown de Leitura**: Para evitar registros duplicados acidentais, o sistema aguarda 2 segundos entre uma leitura e outra.

## Aba: Cadastrar Aluno

Permite adicionar novos alunos ao sistema individualmente.

- **Formulário de Cadastro**:
    - **Nome do Aluno**: Campo para inserir o nome completo do aluno.
    - **ID do Aluno (RA)**: Campo para inserir o Registro Acadêmico (ou qualquer identificador único).
    - **Código da Turma**: Campo para associar o aluno a uma turma específica.
- **Geração de QR Code**:
    - Ao clicar em "Cadastrar e Gerar QR Code", o sistema salva as informações do aluno no arquivo `alunos.csv`.
    - Um QR Code único, contendo o ID do aluno, é gerado e exibido na tela.
- **Salvar QR Code**: Um botão "Salvar QR Code" permite que o usuário salve a imagem do QR Code gerado como um arquivo `.png`. O nome do arquivo é pré-preenchido com a turma e o RA do aluno para fácil identificação.

## Aba: Importar / Exportar

Funcionalidades para gerenciamento de dados em massa.

- **Importar Alunos de JSON**:
    - Um botão permite importar múltiplos alunos a partir de arquivos `.json`.
    - **Localização dos Arquivos**: O sistema busca por arquivos `.json` na pasta `presenca-aluno/data`.
    - **Formato Esperado**: Cada arquivo JSON deve conter uma lista de alunos, e o nome do arquivo (sem a extensão `.json`) deve ser o código da turma. Ex: `294815.json`.
    - **Processo**:
        1. Adiciona novos alunos ao `alunos.csv`.
        2. Atualiza o código da turma de alunos existentes, se necessário.
        3. Gera e salva automaticamente os QR Codes para todos os alunos importados na pasta `qrcodes`.
- **Feedback de Importação**: Uma mensagem de status informa quantos alunos foram importados, quantos foram atualizados e se ocorreram erros durante o processo.
