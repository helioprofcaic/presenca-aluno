# Como Usar o Sistema de Presença

Este guia oferece um passo a passo para utilizar tanto a **aplicação desktop** (para registro de presença) quanto a **interface web** (para visualização e gerenciamento).

## 1. Visão Geral dos Componentes

- **Aplicação Desktop**: Ferramenta principal para o professor em sala de aula. Usa a câmera para ler QR Codes e registrar a presença dos alunos de forma rápida.
- **Interface Web**: Um dashboard acessível por navegador (`http://localhost:5000`) que exibe em tempo real o status de presença de todos os alunos, com gráficos, filtros e funcionalidades de gerenciamento.

## 2. Acessando a Interface Web

1.  **Inicie o Sistema**: Execute `python run.py` no terminal. Isso iniciará tanto o servidor web quanto a aplicação desktop.
2.  **Abra o Navegador**: Acesse `http://localhost:5000`.

### Perfis de Acesso

- **Visitante (Não Logado)**: Vê uma página de apresentação do sistema.
- **Visitante (Logado)**: Acessa o dashboard com dados estatísticos (gráficos e lista de alunos), mas sem informações sensíveis (como RA). Use `usuário: visitante`, `senha: visitante`.
- **Aluno**: Vê apenas seu próprio histórico de presença.
- **Professor**: Vê o dashboard completo, pode filtrar turmas e alunos, mas não vê dados sensíveis.
- **Admin**: Tem acesso total, incluindo o gerenciamento de usuários e a visualização de todos os dados.

## 3. Usando a Aplicação Desktop

### Registrar Presença (Aba "Ler QR Code")

1.  Com a aplicação desktop aberta, clique na aba **"Ler QR Code"**. A câmera será ativada.
2.  Apresente o QR Code de um aluno à câmera.
3.  O sistema registrará a presença e exibirá uma mensagem de confirmação. O status será atualizado quase instantaneamente na interface web.
4.  **Login via QR Code**: Se um professor apresentar seu próprio QR Code, o sistema fará o login automático na interface web e abrirá o navegador.

### Cadastrar Aluno (Aba "Cadastrar Aluno")

1.  Preencha os campos: Nome, RA (ID do Aluno) e Código da Turma.
2.  Clique em **"Cadastrar e Gerar QR Code"**.
3.  O QR Code será exibido. Clique em **"Salvar QR Code"** para guardá-lo.

### Cadastrar Usuário (Aba "Cadastrar Usuário")

Permite criar contas de acesso para a interface web.
1.  Preencha: Nome de usuário, Senha e Perfil (aluno, professor, admin, visitante).
2.  Clique em **"Cadastrar Usuário"**.

### Importar em Lote (Aba "Importar / Exportar")

Esta é a forma mais eficiente de cadastrar turmas inteiras.
1.  **Execute a Importação**: Na aplicação desktop, vá para a aba **"Importar / Exportar"** e clique no botão **"Importar Alunos de JSON"**.
2.  **Selecione os Arquivos**: Uma janela do seu sistema operacional será aberta. Navegue até a pasta onde estão seus arquivos `.json` e selecione um ou mais arquivos de turma para importar. O nome do arquivo (sem a extensão `.json`) deve ser o código da turma (ex: `294815.json`).
3.  **Processo Automático**: O sistema irá:
    - Cadastrar todos os novos alunos no banco de dados.
    - Gerar os QR Codes para cada aluno na pasta `qrcodes/`.
    - **Criar uma conta de usuário para cada aluno**, permitindo que eles acessem a interface web. O nome de usuário e a senha padrão serão o **RA** do aluno.

## 4. Benefícios do Sistema Integrado

- **Visão em Tempo Real**: Professores e gestores podem acompanhar a frequência da escola inteira através do dashboard web, a partir de qualquer computador na mesma rede.
- **Gestão Centralizada**: A interface web permite gerenciar usuários e visualizar dados consolidados, como total de presentes/ausentes e gráficos estatísticos.
- **Flexibilidade**: O registro é feito de forma ágil na sala de aula (desktop), enquanto a análise e o gerenciamento são feitos de forma confortável na interface web.

---

## 5. Benefícios para o Professor (Resumo)
A adoção deste sistema traz vantagens diretas para o dia a dia do professor:

- **Agilidade na Chamada**: Substitui a chamada manual, que consome tempo, por uma leitura de QR Code que leva segundos.
- **Redução de Erros**: Minimiza erros de registro manual, garantindo dados de presença mais precisos.
- **Foco no Ensino**: Libera tempo de aula que seria gasto com tarefas administrativas, permitindo que o professor se concentre no conteúdo e na interação com os alunos.
- **Acompanhamento em Tempo Real**: Através da interface web, o professor pode visualizar o status de presença da turma instantaneamente, mesmo que o registro tenha sido feito por outro responsável na aplicação desktop.

## 6. Benefícios para a Comunidade Escolar (Resumo)

Além do professor, o sistema impacta positivamente toda a comunidade:

- **Modernização de Processos**: Demonstra o compromisso da instituição com a inovação e a tecnologia, melhorando a percepção de pais e alunos.
- **Sustentabilidade**: Reduz drasticamente o uso de papel para listas de chamada e relatórios.
- **Dados Centralizados**: A coordenação pedagógica e a administração escolar podem ter acesso fácil a dados consolidados sobre a frequência, auxiliando na identificação de padrões de ausência e na tomada de decisões estratégicas.
- **Transparência para Alunos e Responsáveis**: A plataforma web permite que alunos (e futuramente, responsáveis) consultem o histórico de presença de forma transparente, promovendo a responsabilidade e o engajamento do estudante com sua própria frequência.
