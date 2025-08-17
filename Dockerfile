FROM python:3.9-slim

# Создаем пользователя для безопасности
RUN useradd -m appuser
WORKDIR /app
RUN chown appuser:appuser /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код и меняем владельца
COPY --chown=appuser:appuser . .

# Переключаемся на непривилегированного пользователя
USER appuser

CMD ["python", "bot.py"]
