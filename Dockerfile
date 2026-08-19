FROM python:3.11-slim

# Evita criação de arquivos .pyc e força flush imediato de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências de build necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto
COPY . .

# Garante permissões de execução do script de inicialização e pasta de dados
RUN chmod +x start.sh && mkdir -p /app/data

# Expõe a porta do Dashboard Streamlit para o Coolify e rede externa
EXPOSE 8501

# Inicia o Bot e o Dashboard juntos
CMD ["./start.sh"]
