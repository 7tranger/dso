#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo -e "${GREEN}=== Запуск Idea Kanban API в Docker ===${NC}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}Предупреждение: файл .env не найден${NC}"
    echo -e "${YELLOW}Создайте .env файл на основе .env.example${NC}"
fi

echo -e "${GREEN}Сборка Docker образа...${NC}"
docker build -t idea-kanban:latest .

echo -e "${GREEN}Запуск контейнера...${NC}"
docker run --rm -d \
    --name idea-kanban \
    -p 8000:8000 \
    --env-file .env \
    idea-kanban:latest

echo -e "${GREEN}Контейнер запущен!${NC}"
echo -e "${GREEN}API доступен на: http://localhost:8000${NC}"
echo -e "${GREEN}Swagger UI: http://localhost:8000/docs${NC}"
echo -e "${GREEN}Health check: http://localhost:8000/health${NC}"

sleep 3
echo -e "${GREEN}Проверка статуса контейнера...${NC}"
docker ps --filter name=idea-kanban

echo -e "${GREEN}Для просмотра логов: docker logs -f idea-kanban${NC}"
echo -e "${GREEN}Для остановки: docker stop idea-kanban${NC}"


