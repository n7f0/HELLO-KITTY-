FROM python:3.11-slim

# Instala ferramentas necessárias para compilar dependências pesadas
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Atualiza o pip para evitar problemas de compatibilidade com pacotes pré-compilados
RUN pip install --upgrade pip

# Instala os pacotes do requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
