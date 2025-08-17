FROM python:3.11-slim

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN useradd -m appuser
WORKDIR /app
RUN chown appuser:appuser /app

# Копирование требований
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY --chown=appuser:appuser . .

# Настройка базы данных
RUN sqlite3 /app/users.db "VACUUM;"

USER appuser

CMD ["python", "bot.py"]
