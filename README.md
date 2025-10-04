# RustDesk Auto-Config Helper

Uma solução simples e segura para implantar o **RustDesk** com configuração centralizada, ideal para equipes de suporte, redes de lojas ou ambientes corporativos que precisam de acesso remoto controlado e escalável.

## Visão Geral

Este projeto automatiza parcialmente a configuração de clientes RustDesk e fornece uma interface gráfica para gerenciar dispositivos remotos.

O sistema é composto por dois componentes principais:
- **`install_and_config_rustdesk.ps1`**: Script PowerShell que instala o RustDesk e envia o ID do dispositivo para um servidor central.
- **`ngrok_server.py`**: Aplicativo Python com interface gráfica (Tkinter) que hospeda uma API local (em ngrok) para receber os dados enviados do RustDesk do cliente, também armazeando os computadores por meio de identificação única. Permitindo se conectar com apenas um clique ao computador remoto (Sem a necessidade de digitar senhas).

## Funcionalidades

- Instalação guiada do RustDesk via PowerShell
- Registro automático do ID do cliente em um servidor central
- Interface gráfica intuitiva para visualizar, conectar, editar e remover dispositivos
- Filtro de busca por apelido ou ID
- Suporte a túnel público via ngrok (opcional)
## Pré-requisitos

- **Windows** (para execução do script PowerShell)
- **Python 3.7+** (para o gerenciador)
- **RustDesk** (será baixado automaticamente pelo script)
- (Opcional) **ngrok** instalado e autenticado (`winget install ngrok`)

## Como Usar

### 1. Inicie o servidor central

```bash
python ngrok_server.py
```

A interface será aberta automaticamente. O console exibirá:
- O URL público via ngrok 

Copie o endpoint `/add_store` — ele será usado pelo script de instalação.

### 2. Execute o script de configuração no cliente

No computador remoto (Windows), execute o PowerShell como administrador e rode:

```powershell
.\install_and_config_rustdesk.ps1
```

O script:
- Baixa e inicia a instalação do RustDesk
- Solicita que você complete a instalação manualmente
- Configura o cliente (com as credenciais definidas dentro do próprio .ps1)
- Captura o ID do dispositivo
- Envia o ID e um apelido para o servidor central

### 3. Gerencie os dispositivos

Volte à interface do `ngrok_server.py`. O novo dispositivo aparecerá automaticamente. Clique em **Conectar** para iniciar uma sessão remota com a senha configurada automaticamente.
