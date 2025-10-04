# ==================================================
# install_and_config_rustdesk_complete_adapted.ps1
# ==================================================

# Configuracoes
$downloadUrl   = 'https://github.com/rustdesk/rustdesk/releases/download/1.4.2/rustdesk-1.4.2-x86_64.exe'
$tempDir       = [IO.Path]::GetTempPath()
$installerPath = Join-Path $tempDir 'rustdesk-1.4.2-x86_64.exe'
$rustdeskDir   = "C:\Program Files\RustDesk"
$rustdeskExe   = Join-Path $rustdeskDir 'rustdesk.exe'
$password     = ""
$configString = ""

# ngrok fixo
$ngrokUrl = ""

# Funcoes
function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $pr = New-Object Security.Principal.WindowsPrincipal($id)
    return $pr.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

# Verifica politica de execucao
if ($PSExecutionPolicyPreference -eq 'Restricted') {
    Write-Host "Politica de execucao restrita. Tentando relancar com Bypass..."
    Start-Process -FilePath 'powershell.exe' -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# Relanca como admin se necessario
if (-not (Test-IsAdmin)) {
    Write-Host "Nao esta em modo administrador. Tentando relancar..."
    Start-Process -FilePath 'powershell.exe' -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# Download do RustDesk se nao existir
if (-not (Test-Path $installerPath)) {
    Write-Host "Baixando RustDesk 1.4.2..."
    try {
        Invoke-WebRequest -Uri $downloadUrl.Trim() -OutFile $installerPath -UseBasicParsing -ErrorAction Stop
        Write-Host "Download concluido: $installerPath"
    } catch {
        Write-Host "Erro ao baixar o instalador: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host "Instalador ja existe: $installerPath"
}

# Abrir instalador para usuario
Write-Host "`nAbrindo instalador do RustDesk..."
Start-Process -FilePath $installerPath
Read-Host "`nQuando terminar a instalacao manual, pressione ENTER para continuar..."

# Verifica se o executavel existe
if (-not (Test-Path $rustdeskExe)) {
    Write-Host "Nao encontrei $rustdeskExe. Verifique a instalacao."
    exit 1
}

$cmdScript = @"
@echo off
cd /d "$rustdeskDir"
rustdesk.exe --password $password
rustdesk.exe --config $configString
exit /b 0
"@

$batPath = Join-Path $env:TEMP "rustdesk_config_$(Get-Random).bat"
Set-Content -Path $batPath -Value $cmdScript -Encoding ASCII
Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$batPath`"" -Wait
Write-Host "Configuracoes aplicadas."

# Obter ID do RustDesk
try {
    $rustdeskId = & $rustdeskExe --get-id 2>&1 | ForEach-Object { $_.ToString().Trim() }
    if ([string]::IsNullOrWhiteSpace($rustdeskId)) {
        Write-Host "Nao foi possivel capturar o ID."
        exit 1
    }
    Write-Host "ID do RustDesk: $rustdeskId"
} catch {
    Write-Host "Erro ao executar rustdesk.exe --get-id"
    exit 1
}

# Perguntar apelido
$nickname = Read-Host "Digite o apelido"

# Enviar dados via POST
Write-Host "`nEnviando dados para: $ngrokUrl"
try {
    $formData = @{
        nickname = $nickname
        id       = $rustdeskId
    }
    $response = Invoke-RestMethod -Uri $ngrokUrl -Method Post -Body $formData -ErrorAction Stop
    if ($null -ne $response) {
        if ($response.status -eq "success") {
            Write-Host "Loja adicionada com sucesso!"
            if ($response.message) { Write-Host $response.message }
        } else {
            Write-Host "Resposta do servidor:"
            Write-Host ($response | ConvertTo-Json -Depth 4)
        }
    } else {
        Write-Host "Requisicao enviada (sem corpo JSON)."
    }
} catch {
    Write-Host "Falha ao enviar dados: $($_.Exception.Message)"
    exit 1
}

# Iniciar RustDesk
Write-Host "`nIniciando RustDesk..."
Start-Process -FilePath $rustdeskExe

Write-Host "`nProcesso concluido!"
