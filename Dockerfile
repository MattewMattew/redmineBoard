# Используем официальный образ Python 3.13 с Alpine
FROM python:3.13-alpine

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем Node.js и npm
RUN apk add --no-cache nodejs npm

# Копируем файлы проекта в рабочую директорию
COPY . /app

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем зависимости Node.js
RUN npm install

# Указываем порт, который будет использоваться приложением
EXPOSE 5000

# Команда для запуска приложения
CMD ["python", "app.py"]