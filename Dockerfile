FROM python:3.11-slim

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN useradd -m appuser
WORKDIR /app

# Копирование требований
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Установка прав на базу данных
RUN touch /app/users.db && \
    chown appuser:appuser /app/users.db && \
    chmod 644 /app/users.db

USER appuser

CMD ["python", "bot.py"]
