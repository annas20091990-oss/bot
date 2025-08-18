FROM python:3.11-slim

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя
RUN useradd -m appuser
WORKDIR /app

# Установка прав на рабочую директорию
RUN chown -R appuser:appuser /app

# Копирование требований
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Установка владельца для всех файлов
RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "bot.py"]
