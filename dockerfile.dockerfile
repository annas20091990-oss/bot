FROM python:3.9-slim

WORKDIR /app

# Копируем секреты в специальную директорию
COPY . /app
RUN --mount=type=secret,id=env,dst=/etc/secrets/.env \
    cp /etc/secrets/.env .env && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
