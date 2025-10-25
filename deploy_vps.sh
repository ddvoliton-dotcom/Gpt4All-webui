#!/bin/bash

# Скрипт для автоматизации развертывания на VPS

# Переменные
MODEL_PATH="/app/api/models/model.bin"

# Проверка наличия файла модели
if [ ! -f "$MODEL_PATH" ]; then
  echo "Файл модели не найден: $MODEL_PATH"
  exit 1
fi

# Установка зависимостей
apt-get update
apt-get install -y docker-compose

# Запуск контейнера
docker-compose up -d

# Вывод .onion адреса
echo "Служба развернута. Получите .onion адрес через Tor logs."