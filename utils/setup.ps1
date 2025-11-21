# setup.ps1
# Script para configurar o ambiente de desenvolvimento para os aplicativos presenca-aluno e presenca-aluno-exporter.

function SetupPythonEnvironment {
    param (
        [string]$AppPath
    )

    Write-Host "Configurando ambiente para: $AppPath"
    Set-Location $AppPath

    # O ambiente virtual será criado dentro da pasta do próprio aplicativo
    $venvPath = Join-Path $AppPath ".venv"
    $requirementsPath = Join-Path $AppPath "requirements.txt"

    # Criar ambiente virtual se não existir
    if (-not (Test-Path $venvPath)) {
        Write-Host "Criando ambiente virtual em $venvPath..."
        python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Falha ao criar o ambiente virtual."
            exit 1
        }
        Write-Host "Ambiente virtual criado com sucesso!"
    } else {
        Write-Host "Ambiente virtual já existe em $venvPath."
    }

    # Ativar ambiente virtual e instalar dependências
    if (Test-Path (Join-Path $venvPath "Scripts\Activate.ps1")) {
        Write-Host "Ativando ambiente virtual..."
        . (Join-Path $venvPath "Scripts\Activate.ps1")
    } elseif (Test-Path (Join-Path $venvPath "bin\activate")) {
        Write-Host "Ativando ambiente virtual (Linux/macOS)..."
        . (Join-Path $venvPath "bin\activate")
    } else {
        Write-Error "Não foi possível encontrar o script de ativação do ambiente virtual."
        exit 1
    }

    if (Test-Path $requirementsPath) {
        Write-Host "Instalando dependências de $requirementsPath..."
        pip install -r $requirementsPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Falha ao instalar as dependências."
            exit 1
        }
        Write-Host "Dependências instaladas com sucesso!"
    } else {
        Write-Warning "Arquivo requirements.txt não encontrado em $AppPath. Nenhuma dependência instalada."
    }

    Write-Host "Configuração para $AppPath concluída."
    Write-Host ""
}

# O caminho do aplicativo é o diretório pai da pasta 'utils'
$appPath = (Get-Item (Join-Path $PSScriptRoot "..")).FullName
SetupPythonEnvironment -AppPath $appPath

Write-Host "--------------------------------------------------"
Write-Host "Configuração do ambiente de desenvolvimento concluída."
Write-Host ""
Write-Host "Para executar o aplicativo 'presenca-aluno':"
Write-Host "  1. Navegue até o diretório: cd $appPath"
Write-Host "  2. Ative o ambiente virtual: .\.venv\Scripts\Activate.ps1"
Write-Host "  3. Execute o script principal: python run.py"
Write-Host ""
Write-Host "--------------------------------------------------"
