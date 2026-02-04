FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код бота
COPY . .

# Порт (Render требует чтобы приложение слушало PORT из env)
# Но наш бот не HTTP-сервер, поэтому просто экспортируем для совместимости
ENV PORT=8080

# Запускаем бот
CMD ["python", "main.py"]
