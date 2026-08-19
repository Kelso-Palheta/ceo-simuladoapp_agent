#!/bin/bash
set -e

# Garante a existência do diretório de dados persistentes
mkdir -p /app/data

echo "=========================================="
echo "🏛️ SIMULADOAPP — INICIANDO SERVIÇOS"
echo "=========================================="

# Inicia o Bot do Telegram em background
echo "🤖 Iniciando Bot do Telegram..."
python bot.py &
BOT_PID=$!

# Função para encerrar os processos caso o container receba sinal de término
cleanup() {
    echo "🛑 Encerrando serviços..."
    kill $BOT_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

echo "🖥️ Iniciando Dashboard Streamlit na porta 8501..."
# Inicia o Dashboard Web em primeiro plano (mantendo o container ativo e respondendo aos health checks)
streamlit run dashboard.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false

# Se o Streamlit for finalizado, encerra o bot
kill $BOT_PID 2>/dev/null || true
