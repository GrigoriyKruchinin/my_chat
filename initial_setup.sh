#!/bin/bash

set -e

echo -e "\n\n\nНачало начальной настройки...\n\n\n"

echo -e "\n\n\nСборка и запуск контейнеров...\n\n\n"
docker-compose up --build -d db app

echo -e "\n\n\nПрименение миграций...\n\n\n"
docker-compose run app alembic upgrade head

echo -e "\n\n\nНачальная настройка завершена. Приложение запущено.\n\n\n"
docker-compose up app

echo -e "\n\n\nПриложение остановлено.\n\n\n"