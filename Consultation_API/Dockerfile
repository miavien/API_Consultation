# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Открываем порт приложения
EXPOSE 8000

# Запускаем команду для старта приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]