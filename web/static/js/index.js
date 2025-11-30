document.addEventListener('DOMContentLoaded', function () {
    // =================================================================
    // BLOCO DE INICIALIZAÇÃO E CACHE DE DADOS
    // =================================================================
    let allStudentsData = []; // Variável para armazenar em cache os dados originais de todos os alunos.

    // =================================================================
    // BLOCO DE UTILITÁRIOS DA UI
    // =================================================================

    /**
     * Exibe uma mensagem de flash dinâmica no topo da página.
     * @param {string} message - A mensagem a ser exibida.
     * @param {string} category - A categoria do alerta (ex: 'success', 'danger', 'warning').
     */
    function showFlashMessage(message, category) {
        const container = document.getElementById('flash-container');
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${category} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        container.appendChild(alertDiv);

        // Remove a mensagem após 5 segundos
        setTimeout(() => {
            const alertInstance = new bootstrap.Alert(alertDiv);
            alertInstance.close();
        }, 5000);
    }


    // =================================================================
    // BLOCO DE BUSCA DE DADOS (API)
    // =================================================================

    // Função assíncrona para buscar os dados de presença da API do Flask.
    async function fetchPresenceData(userRole, apiBaseUrl) {
        try {
            // Constrói a URL completa para a API, garantindo que funcione em dispositivos móveis.
            const apiUrl = `${apiBaseUrl}/api/presence_data`;
            console.log("Buscando dados de:", apiUrl); // Log para depuração
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json(); // Converte a resposta para JSON. 
            allStudentsData = data; // Armazena os dados no cache local.
            
            // Popula os filtros apenas se a barra de filtro existir (visível para o professor).
            if (document.getElementById('filterTurma')) {
                populateFilterOptions(allStudentsData); 
            }

            updateDashboardStats(allStudentsData); // Calcula e exibe as estatísticas

            renderPresenceData(allStudentsData); // Renderiza os dados na tela pela primeira vez.
        } catch (error) {
            console.error('Error fetching presence data:', error);
            showFlashMessage('Erro ao carregar os dados dos alunos.', 'danger');
        } finally {
            // Torna o corpo da página visível após a tentativa de carregar os dados
            document.getElementById('page-body').style.visibility = 'visible';
        }
    }

    // =================================================================
    // BLOCO DE ESTATÍSTICAS E GRÁFICOS
    // =================================================================

    let presenceChartInstance = null; // Variável para manter a instância do gráfico

    /**
     * Calcula as estatísticas gerais e atualiza os cards e o gráfico.
     * @param {Array} data - Os dados de todos os alunos.
     */
    function updateDashboardStats(data) {
        const totalAlunos = data.length;
        const presentes = data.filter(a => a.status_presenca !== 'Ausente').length;
        const ausentes = totalAlunos - presentes;
        const totalTurmas = [...new Set(data.map(aluno => aluno.nome_turma || 'Sem Turma'))].length;

        // Atualiza os cards
        document.getElementById('stats-total-alunos').textContent = totalAlunos;
        document.getElementById('stats-total-turmas').textContent = totalTurmas;
        document.getElementById('stats-presentes').textContent = presentes;
        document.getElementById('stats-ausentes').textContent = ausentes;

        // Atualiza o gráfico de pizza
        const ctx = document.getElementById('presenceChart').getContext('2d');
        if (presenceChartInstance) {
            presenceChartInstance.destroy(); // Destrói o gráfico anterior para criar um novo
        }
        presenceChartInstance = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Presentes', 'Ausentes'],
                datasets: [{
                    label: 'Status de Presença',
                    data: [presentes, ausentes],
                    backgroundColor: ['#198754', '#dc3545'],
                    borderColor: ['#fff', '#fff'],
                    borderWidth: 2
                }]
            },
            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'top' } } }
        });
    }

    // =================================================================
    // BLOCO DE POPULAÇÃO DOS FILTROS
    // =================================================================

    // Função para popular o menu suspenso (dropdown) de filtro de turmas.
    function populateFilterOptions(data) {
        const filterTurmaSelect = document.getElementById('filterTurma');
        // Procede apenas se o elemento de filtro existir.
        if (!filterTurmaSelect) return;

        const currentTurma = filterTurmaSelect.value;

        // Cria uma lista de turmas únicas a partir dos dados dos alunos e as ordena.
        const uniqueTurmas = [...new Set(data.map(aluno => aluno.nome_turma || 'Sem Turma'))].sort();

        // Limpa as opções existentes, exceto a opção "Todas".
        filterTurmaSelect.innerHTML = '<option value="">Todas</option>';

        // Adiciona cada turma como uma nova opção no dropdown.
        uniqueTurmas.forEach(turma => {
            const option = document.createElement('option');
            option.value = turma;
            option.textContent = turma;
            filterTurmaSelect.appendChild(option);
        });

        // Restaura a seleção anterior se ela ainda existir
        if (uniqueTurmas.includes(currentTurma)) {
            filterTurmaSelect.value = currentTurma;
        }
    }

    // =================================================================
    // BLOCO DE RENDERIZAÇÃO DA INTERFACE (ABAS E TABELAS)
    // =================================================================

    // Função principal para renderizar os dados de presença, agrupando-os por turma em abas.
    function renderPresenceData(data) {
        const turmaTabs = document.getElementById('turmaTabs');
        const turmaTabContent = document.getElementById('turmaTabContent');
        const noStudentsAlert = document.getElementById('no-students-alert');
        
        // Limpa o conteúdo existente antes de renderizar novamente.
        turmaTabs.innerHTML = '';
        turmaTabContent.innerHTML = '';

        // Lógica para exibir/ocultar filtros e controles com base na existência de alunos.
        const hasAnyStudent = allStudentsData.length > 0;
        const filterBarElement = document.getElementById('filter-bar');
        if (filterBarElement) {
            filterBarElement.style.display = hasAnyStudent ? 'block' : 'none';
        }
        const controlsElement = document.querySelector('.controls');
        if (controlsElement) {
            controlsElement.style.display = hasAnyStudent ? 'block' : 'none';
        }

        // Se não houver dados (seja no geral ou após filtrar), mostra o alerta e para.
        if (data.length === 0) {
            // Se não houver nenhum aluno cadastrado, a mensagem é "Nenhum aluno encontrado".
            // Se houver alunos, mas o filtro não retornou nada, a mensagem é mais específica.
            if (hasAnyStudent) {
                noStudentsAlert.textContent = 'Nenhum aluno corresponde aos critérios do filtro.';
            } else {
                noStudentsAlert.textContent = 'Nenhum aluno encontrado no banco de dados.';
            }
            noStudentsAlert.style.display = 'block';
            return;
        } else {
            noStudentsAlert.style.display = 'none';
        }

        // Agrupa os dados dos alunos por turma.
        const groupedByTurma = data.reduce((acc, aluno) => {
            const turma = aluno.nome_turma || 'Sem Turma';
            if (!acc[turma]) {
                acc[turma] = [];
            }
            acc[turma].push(aluno);
            return acc;
        }, {});

        const sortedTurmas = Object.keys(groupedByTurma).sort();
        let isFirstTab = true;

        // Pega as permissões do corpo do HTML
        const userRole = document.body.dataset.userRole;
        const canViewSensitiveData = document.body.dataset.canViewSensitiveData === 'true';

        for (const turma of sortedTurmas) {
            const turmaId = `turma-${turma.replace(/\s+/g, '-')}`; // ID único para a aba e seu conteúdo.
            
            // Cria o item de navegação (o botão da aba).
            const navItem = document.createElement('li');
            navItem.classList.add('nav-item');
            navItem.setAttribute('role', 'presentation');
            navItem.innerHTML = `
                <button class="nav-link ${isFirstTab ? 'active' : ''}" id="${turmaId}-tab" data-bs-toggle="tab" 
                        data-bs-target="#${turmaId}" type="button" role="tab" aria-controls="${turmaId}"
                        aria-selected="${isFirstTab ? 'true' : 'false'}">
                    ${turma} <span class="badge bg-secondary ms-1" id="count-${turmaId}">${groupedByTurma[turma].length}</span>
                </button>
            `;
            turmaTabs.appendChild(navItem);

            // Cria o painel de conteúdo da aba (que conterá a tabela).
            const tabPane = document.createElement('div');
            tabPane.classList.add('tab-pane', 'fade');
            if (isFirstTab) {
                tabPane.classList.add('show', 'active');
            }
            tabPane.setAttribute('id', turmaId);
            tabPane.setAttribute('role', 'tabpanel');
            tabPane.setAttribute('aria-labelledby', `${turmaId}-tab`);
            tabPane.innerHTML = `
                <table class="table table-striped table-hover mt-3">
                    <thead class="table-dark"> 
                        <tr>
                            ${canViewSensitiveData ? '<th>RA</th>' : ''}
                            <th>Nome</th>
                            <th>Status</th>
                            <th>Entrada</th>
                            <th>Saída</th>
                            <th>Ações</th>
                        </tr>
                    </thead> 
                    <tbody>
                        ${groupedByTurma[turma].map(aluno => {
                            let statusBadgeClass = 'bg-danger'; // Padrão para 'Ausente'
                            switch (aluno.status_presenca) {
                                case 'Presente':
                                    statusBadgeClass = 'bg-success';
                                    break;
                                case 'Apenas Entrada':
                                    statusBadgeClass = 'bg-info text-dark';
                                    break;
                                case 'Atraso':
                                case 'Saída Antecipada':
                                case 'Presente (Incompleto)':
                                    statusBadgeClass = 'bg-warning text-dark';
                                    break;
                            }

                            return `
                            <tr>
                                ${canViewSensitiveData ? `<td data-label="RA"><a href="#" class="qr-code-trigger" data-ra="${aluno.ra}" data-nome="${aluno.nome}">${aluno.ra}</a></td>` : ''}
                                <td>${aluno.nome}</td>
                                <td>
                                    <span class="badge ${statusBadgeClass}">
                                        ${aluno.status_presenca}
                                    </span>
                                </td>
                                <td>${aluno.timestamp_entrada ? new Date(aluno.timestamp_entrada).toLocaleTimeString('pt-BR') : 'N/A'}</td>
                                <td>${aluno.timestamp_saida ? new Date(aluno.timestamp_saida).toLocaleTimeString('pt-BR') : 'N/A'}</td>
                                <td>
                                    ${userRole === 'professor' ? `<a href="/aluno/${aluno.ra}" class="btn btn-sm btn-info">Ver Histórico</a>` : ''}
                                </td>
                            </tr>
                        `}).join('')}
                    </tbody>
                </table>
            `;
            turmaTabContent.appendChild(tabPane);

            isFirstTab = false;
        }

        // Adiciona event listeners aos novos links de RA
        document.querySelectorAll('.qr-code-trigger').forEach(trigger => {
            trigger.addEventListener('click', showStudentQrCode);
        });
    }

    // =================================================================
    // BLOCO DE LÓGICA DE FILTRAGEM
    // =================================================================

    // Função para aplicar os filtros selecionados pelo usuário.
    function applyFilters(event) {
        const filterTurma = document.getElementById('filterTurma').value;
        const filterNameRa = document.getElementById('filterNameRa').value.toLowerCase();
        const filterStatus = document.getElementById('filterStatus').value;

        // Se o filtro de turma foi alterado, ativa a aba correspondente.
        if (event && event.target.id === 'filterTurma') {
            const turmaId = `turma-${filterTurma.replace(/\s+/g, '-')}`;
            const tabButton = document.getElementById(`${turmaId}-tab`);
            if (tabButton) {
                // Cria uma instância do Tab do Bootstrap e a exibe.
                const tab = new bootstrap.Tab(tabButton);
                tab.show();
            }
        }

        // Itera sobre todas as linhas de todas as tabelas para aplicar os filtros de texto e status.
        const allRows = document.querySelectorAll('#turmaTabContent tbody tr');
        let visibleStudentsByTurma = {};

        allRows.forEach(row => {
            const ra = row.querySelector('td[data-label="RA"]').textContent.toLowerCase();
            const nome = row.cells[1].textContent.toLowerCase();
            const status = row.cells[2].textContent.trim();
            const turmaPane = row.closest('.tab-pane');
            const studentTurma = turmaPane.id.replace('turma-', '').replace(/-/g, ' ');

            const matchesTurma = filterTurma === '' || studentTurma === filterTurma;
            const matchesNameRa = filterNameRa === '' || nome.includes(filterNameRa) || ra.includes(filterNameRa);
            const matchesStatus = filterStatus === '' || status === filterStatus;

            if (matchesTurma && matchesNameRa && matchesStatus) {
                row.style.display = ''; // Mostra a linha
                if (!visibleStudentsByTurma[turmaPane.id]) {
                    visibleStudentsByTurma[turmaPane.id] = 0;
                }
                visibleStudentsByTurma[turmaPane.id]++;
            } else {
                row.style.display = 'none'; // Esconde a linha
            }
        });

        // Atualiza os contadores de alunos visíveis em cada aba.
        document.querySelectorAll('#turmaTabs .badge').forEach(badge => {
            const turmaId = badge.id.replace('count-', '');
            badge.textContent = visibleStudentsByTurma[turmaId] || 0;
        });
    }

    // =================================================================
    // BLOCO DE AÇÕES (EXPORTAR, IMPRIMIR, SALVAR, ETC.)
    // =================================================================

    // Função para exportar os dados da aba ativa para um arquivo CSV.
    function exportToCsv() {
        const activeTabContent = document.querySelector('.tab-pane.active');
        if (!activeTabContent) {
            alert('Nenhuma turma selecionada para exportar.');
            return;
        }

        const rows = activeTabContent.querySelectorAll('table tr');
        let csvContent = "data:text/csv;charset=utf-8,";
        
        // Adiciona a linha de cabeçalho.
        const headers = Array.from(rows[0].querySelectorAll('th')).map(th => `"${th.innerText.trim()}"`).join(',');
        csvContent += headers + "\r\n";

        // Adiciona as linhas de dados.
        for (let i = 1; i < rows.length; i++) {
            const cols = rows[i].querySelectorAll('td');
            const rowData = Array.from(cols).map(col => {
                // Limpa o texto da célula.
                let cellText = col.innerText.trim();
                // Para a coluna "Ações", não queremos o texto do botão.
                if (col.querySelector('a.btn')) {
                    return '""'; // Retorna uma string vazia entre aspas.
                }
                return `"${cellText.replace(/"/g, '""')}"`;
            }).slice(0, -1).join(','); // Exclude the last column (Ações)
            csvContent += rowData + "\r\n";
        }

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        
        const turmaName = activeTabContent.id.replace('turma-', '');
        link.setAttribute("download", `presenca_turma_${turmaName}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    /**
     * Abre uma nova janela com os QR Codes de todos os alunos da aba ativa, pronta para impressão.
     */
    function printQrCodes() {
        const activeTabContent = document.querySelector('.tab-pane.active');
        if (!activeTabContent) {
            showFlashMessage('Nenhuma turma selecionada para imprimir QR Codes.', 'warning');
            return;
        }

        const turmaName = activeTabContent.id.replace('turma-', '').replace(/-/g, ' ');        
        const rows = activeTabContent.querySelectorAll('tbody tr');
        const studentsInTurma = [];

        rows.forEach(row => {
            // Pega o RA do link dentro da primeira célula de dados (td)
            const raElement = row.querySelector('td[data-label="RA"] a');
            if (raElement) {
                const ra = raElement.dataset.ra;
                // Encontra o aluno correspondente nos dados completos para obter todas as informações
                const studentData = allStudentsData.find(s => s.ra === ra);
                if (studentData) {
                    studentsInTurma.push(studentData);
                }
            }
        });

        if (studentsInTurma.length === 0) {
            showFlashMessage('Não há alunos nesta turma para imprimir QR Codes.', 'info');
            return;
        }

        const printWindow = window.open('', '', 'height=800,width=1000');
        printWindow.document.write('<html><head><title>QR Codes - Turma ' + turmaName + '</title>');
        printWindow.document.write('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">');
        printWindow.document.write(`
            <style>
                body { padding: 20px; }
                @page {
                    size: A4;
                    margin: 20mm;
                }
                .qr-card { 
                    page-break-inside: avoid; 
                    border: 1px solid #ccc; 
                    border-radius: 8px; 
                    padding: 10px; 
                    margin: 10px; 
                    width: calc(33.333% - 20px); 
                    float: left; 
                    box-sizing: border-box;
                    text-align: center;
                }
                .qr-card img { 
                    max-width: 150px; 
                    height: auto; 
                    margin-bottom: 10px;
                }
                .student-name { font-weight: bold; margin-top: 5px; }
                @media print {
                    body { -webkit-print-color-adjust: exact; }
                    .no-print { display: none; }
                }
            </style>
        `);
        printWindow.document.write('</head><body>');
        printWindow.document.write(`<h1 class="mb-4">QR Codes para Presença - Turma: ${turmaName}</h1>`);
        printWindow.document.write('<p class="no-print">Use a função de impressão do seu navegador (Ctrl+P) para imprimir esta página.</p><hr>');

        studentsInTurma.forEach(aluno => {
            printWindow.document.write(`
                <div class="qr-card">
                    <img src="/qrcodes/turma_${aluno.codigo_turma}_ra_${aluno.ra}.png"
                         alt="QR Code do aluno ${aluno.nome}"
                         onerror="this.style.display='none'; this.parentElement.innerHTML += '<p class=\\'text-danger\\'>Imagem não encontrada.</p>';">
                    <div class="student-name">${aluno.nome}</div>
                    <div class="student-ra text-muted">${aluno.ra}</div>
                </div>
            `);
        });

        printWindow.document.write('</body></html>');
        printWindow.document.close();
    }

    // Função para imprimir a tabela da aba ativa.
    function printTable() {
        const activeTabContent = document.querySelector('.tab-pane.active');
        if (!activeTabContent) {
            alert('Nenhuma turma selecionada para imprimir.');
            return;
        }

        const turmaName = activeTabContent.id.replace('turma-', '');
        const printWindow = window.open('', '', 'height=600,width=800');
        printWindow.document.write('<html><head><title>Imprimir Presença</title>');
        // Link para o CSS do Bootstrap para manter o estilo na impressão.
        printWindow.document.write('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">');
        printWindow.document.write('<style>body { padding: 20px; } .badge { font-size: 1em; } a { display: none; } table { margin-top: 0 !important; }</style>');
        printWindow.document.write('</head><body>');
        printWindow.document.write(`<h1>Lista de Presença - Turma: ${turmaName}</h1>`);
        
        const tableToPrint = activeTabContent.querySelector('table').cloneNode(true);
        // Remove a coluna "Ações" do cabeçalho e do corpo da tabela para a impressão.
        Array.from(tableToPrint.querySelectorAll('tr')).forEach(row => {
            row.deleteCell(-1); // Delete the last cell
        });

        printWindow.document.write(tableToPrint.outerHTML);
        printWindow.document.write('</body></html>');
        printWindow.document.close();
        
        printWindow.onload = function() {
            printWindow.focus();
            printWindow.print();
            printWindow.close();
        };
    }

    // Função de placeholder para salvar no banco de dados (requer um endpoint no backend).
    async function saveToDatabase() {
        alert('Funcionalidade de salvar alterações ainda não implementada.');
    }

    /**
     * Exibe um modal com o QR Code de um aluno específico.
     * @param {Event} event - O evento de clique que acionou a função.
     */
    function showStudentQrCode(event) {
        event.preventDefault();
        const studentRa = event.target.dataset.ra;
        const studentName = event.target.dataset.nome;

        // Encontra o aluno nos dados cacheados para obter o código da turma
        const student = allStudentsData.find(s => s.ra === studentRa);
        if (!student) {
            showFlashMessage('Não foi possível encontrar os dados completos do aluno.', 'danger');
            return;
        }

        const modal = new bootstrap.Modal(document.getElementById('qrCodeModal'));
        const qrContainer = document.getElementById('qr-code-container');        
        
        // Limpa o QR code anterior
        qrContainer.innerHTML = '';

        document.getElementById('qr-modal-student-name').textContent = studentName;
        document.getElementById('qr-modal-student-ra').textContent = `RA: ${studentRa}`;

        // Cria a URL para a imagem do QR Code
        const qrImageUrl = `/qrcodes/turma_${student.codigo_turma}_ra_${student.ra}.png`;

        // Cria o elemento de imagem e o adiciona ao contêiner
        const imgElement = document.createElement('img');
        imgElement.src = qrImageUrl;
        imgElement.alt = `QR Code para ${studentName}`;
        imgElement.className = 'img-fluid'; // Garante que a imagem seja responsiva dentro do modal
        qrContainer.appendChild(imgElement);

        modal.show();
    }

    /**
     * Envia uma requisição para repopular o banco de dados de alunos.
     * Pede confirmação ao usuário antes de proceder.
     */
    async function repopulateDatabase() {
        const confirmation = confirm(
            'Você tem certeza que deseja repopular o banco de dados?\n\n' +
            'ATENÇÃO: Todos os alunos e registros de presença existentes serão APAGADOS. ' +
            'Os alunos serão recarregados a partir dos arquivos JSON originais.'
        );

        if (!confirmation) {
            return;
        }

        try {
            const response = await fetch('/api/repopulate_students', { method: 'POST' });
            const result = await response.json();

            if (response.ok) {
                showFlashMessage(result.message, 'success');
            } else {
                throw new Error(result.message || 'Erro desconhecido ao repopular o banco de dados.');
            }
        } catch (error) {
            console.error('Error repopulating database:', error);
            showFlashMessage(error.message, 'danger');
        } finally {
            // Recarrega os dados da tabela para refletir as mudanças.
            const userRole = document.body.dataset.userRole;
            const apiBaseUrl = document.body.dataset.apiBaseUrl;
            fetchPresenceData(userRole, apiBaseUrl);
        }
    }


    // =================================================================
    // BLOCO DE INICIALIZAÇÃO E EVENT LISTENERS
    // =================================================================

    // Pega a role do usuário a partir do atributo data-* no body.
    const userRole = document.body.dataset.userRole;
    const apiBaseUrl = document.body.dataset.apiBaseUrl;

    // Busca os dados iniciais assim que a página é carregada, passando a role.
    fetchPresenceData(userRole, apiBaseUrl);


        // Adiciona os "escutadores de eventos" aos botões de filtro, impressão, etc.
    // Anexa os eventos apenas se os elementos existirem (visíveis para o professor).
    const filterTurma = document.getElementById('filterTurma');
    if (filterTurma) {
        filterTurma.addEventListener('change', (e) => applyFilters(e));
    }
    const filterNameRa = document.getElementById('filterNameRa');
    if (filterNameRa) {
        filterNameRa.addEventListener('keyup', (e) => applyFilters(e));
    }
    const filterStatus = document.getElementById('filterStatus');
    if (filterStatus) {
        filterStatus.addEventListener('change', (e) => applyFilters(e));
    }
    const printButton = document.getElementById('printButton');
    if (printButton) {
        printButton.addEventListener('click', printTable);
    }
    const exportCsvButton = document.getElementById('exportCsvButton');
    if (exportCsvButton) {
        exportCsvButton.addEventListener('click', exportToCsv);
    }
    const printQrCodesButton = document.getElementById('printQrCodesButton');
    if (printQrCodesButton) {
        printQrCodesButton.addEventListener('click', printQrCodes);
    }
    const saveButton = document.getElementById('saveButton');
    if (saveButton) {
        saveButton.addEventListener('click', saveToDatabase);
    }
    const repopulateDbButton = document.getElementById('repopulateDbButton');
    if (repopulateDbButton) {
        repopulateDbButton.addEventListener('click', repopulateDatabase);
    }
});
