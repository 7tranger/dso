#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Тестирование контейнера Idea Kanban API ===${NC}"

CONTAINER_NAME="idea-kanban-test"
IMAGE_NAME="idea-kanban:latest"
HEALTH_ENDPOINT="http://localhost:8000/health"
MAX_WAIT=60
SLEEP_INTERVAL=2

cleanup() {
    echo -e "${YELLOW}Очистка...${NC}"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

trap cleanup EXIT

if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo -e "${RED}Ошибка: образ $IMAGE_NAME не найден${NC}"
    echo -e "${YELLOW}Сначала соберите образ: docker build -t $IMAGE_NAME .${NC}"
    exit 1
fi

echo -e "${GREEN}Запуск тестового контейнера...${NC}"
docker run --rm -d \
    --name "$CONTAINER_NAME" \
    -p 8000:8000 \
    -e JWT_SECRET="test-secret-key-minimum-16-characters" \
    -e DATABASE_URL="sqlite:///./test.db" \
    -e SCORE_API_BASE="https://example.com" \
    "$IMAGE_NAME"

echo -e "${GREEN}[1/4] Проверка пользователя процесса...${NC}"
USER_ID=$(docker exec "$CONTAINER_NAME" id -u)
if [ "$USER_ID" != "0" ]; then
    echo -e "${GREEN}Пользователь не root (UID: $USER_ID)${NC}"
else
    echo -e "${RED}Ошибка: процесс запущен от root (UID: $USER_ID)${NC}"
    exit 1
fi

echo -e "${GREEN}[2/4] Ожидание готовности контейнера (healthcheck)...${NC}"
ELAPSED=0
HEALTHY=false

while [ $ELAPSED -lt $MAX_WAIT ]; do
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "starting")

    if [ "$HEALTH_STATUS" = "healthy" ]; then
        HEALTHY=true
        echo -e "${GREEN}Контейнер здоров${NC}"
        break
    fi

    if [ "$HEALTH_STATUS" = "unhealthy" ]; then
        echo -e "${RED}Контейнер нездоров${NC}"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi

    echo -e "${YELLOW}Ожидание... (${ELAPSED}s/${MAX_WAIT}s) - статус: $HEALTH_STATUS${NC}"
    sleep $SLEEP_INTERVAL
    ELAPSED=$((ELAPSED + SLEEP_INTERVAL))
done

if [ "$HEALTHY" = false ]; then
    echo -e "${RED}✗ Таймаут ожидания healthcheck${NC}"
    docker logs "$CONTAINER_NAME"
    exit 1
fi

echo -e "${GREEN}[3/4] Проверка HTTP endpoint /health...${NC}"
if command -v curl >/dev/null 2>&1; then
    if curl -f -s "$HEALTH_ENDPOINT" >/dev/null; then
        echo -e "${GREEN}Endpoint /health доступен${NC}"
    else
        echo -e "${RED}Endpoint /health недоступен${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}curl не найден, пропускаем HTTP проверку${NC}"
fi

echo -e "${GREEN}[4/4] Проверка процессов в контейнере...${NC}"
PROCESSES=$(docker exec "$CONTAINER_NAME" ps aux | grep -v "PID" | wc -l)
if [ "$PROCESSES" -gt 0 ]; then
    echo -e "${GREEN}Процессы запущены (найдено: $PROCESSES)${NC}"
else
    echo -e "${RED}Процессы не найдены${NC}"
    exit 1
fi

echo -e "${GREEN}=== Итоговая информация ===${NC}"
echo -e "${GREEN}Контейнер: $CONTAINER_NAME${NC}"
echo -e "${GREEN}Пользователь: $(docker exec "$CONTAINER_NAME" id -un) (UID: $USER_ID)${NC}"
echo -e "${GREEN}Health статус: $(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME")${NC}"
echo -e "${GREEN}Все проверки пройдены успешно! ${NC}"
