#!/bin/bash

# Script para testar publicação de mensagens MQTT no HiveMQ
# Execute este script para simular dados do DHT22

echo "=== Teste de Publicação MQTT ==="
echo ""

# Esperar o container estar pronto
echo "Aguardando HiveMQ ficar pronto..."
sleep 5

# Publicar alguns valores de teste
echo "Publicando dados de teste..."

for i in {1..10}; do
    TEMP=$(echo "scale=1; 20 + $RANDOM % 10" | bc)
    HUMIDITY=$(echo "scale=1; 40 + $RANDOM % 30" | bc)
    
    MESSAGE="{\"temperature\": $TEMP, \"humidity\": $HUMIDITY, \"deviceId\": \"esp32-dht22\", \"location\": \"sala\"}"
    
    echo "Mensagem $i: $MESSAGE"
    
    docker-compose exec -T hivemq mosquitto_pub \
        -h localhost \
        -t opaiot/temperature \
        -m "$MESSAGE"
    
    sleep 2
done

echo ""
echo "✓ Teste concluído!"
echo ""
echo "Verifique os dados em:"
echo "  - Backend API: http://localhost:3000/api/latest"
echo "  - Grafana: http://localhost:3001"
