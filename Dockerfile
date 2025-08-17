FROM python:3.11-slim

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя
RUN useradd -m appuser
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Устанавливаем владельца для всей директории
RUN chown -R appuser:appuser /app

# Создаем файл БД и устанавливаем права
RUN touch /app/users.db && \
    chown appuser:appuser /app/users.db && \
    chmod 664 /app/users.db

# Переключаемся на пользователя appuser
USER appuser

CMD ["python", "bot.py"]
