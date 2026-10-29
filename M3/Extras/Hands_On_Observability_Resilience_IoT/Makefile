.PHONY: up down logs broker-down broker-up burst ps clean

up:
	UID=$$(id -u) GID=$$(id -g) docker compose up -d --build
	@echo ""
	@echo "Grafana:    http://localhost:3000  (admin/admin, ou sem login)"
	@echo "Prometheus: http://localhost:9090"

down:
	docker compose down

# Experimento 1 --- indisponibilidade do broker
broker-down:
	docker compose stop mosquitto

broker-up:
	docker compose start mosquitto

# Experimento 2 --- sobrecarga do consumidor: injeta uma rajada de ~30 msg/s
# por 8 segundos, com um device_id próprio, sem interromper o publisher
# principal (que continua publicando na taxa normal).
burst:
	docker compose run --rm -e RATE=30 -e DURATION=8 -e DEVICE_ID=burst-01 publisher

logs:
	docker compose logs -f publisher consumer mosquitto

ps:
	docker compose ps

clean:
	docker compose down -v
