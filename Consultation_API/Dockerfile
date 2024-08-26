# Используем официальный образ Python как базовый
FROM python:3.12-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта в рабочую директорию контейнера
COPY . /app/

# Выполняем миграции и запускаем сервер
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]