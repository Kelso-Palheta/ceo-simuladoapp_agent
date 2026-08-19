#!/bin/bash
set -e

echo "🚀 Iniciando setup do SimuladoApp Agent no servidor..."

# 1. Atualizar pacotes do sistema
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# 2. Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual Python..."
    python3 -m venv venv
fi

# 3. Instalar dependências
echo "📥 Instalando dependências..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Configurar Systemd para rodar 24/7
echo "⚙️ Configurando serviço systemd..."
sudo cp simuladoapp.service /etc/systemd/system/simuladoapp.service
sudo systemctl daemon-reload
sudo systemctl enable simuladoapp.service
sudo systemctl restart simuladoapp.service

echo "✅ Sucesso! O bot está rodando em segundo plano 24/7."
echo "Para ver os logs ao vivo, execute: sudo journalctl -u simuladoapp.service -f"
