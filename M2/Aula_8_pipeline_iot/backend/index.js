const mqtt = require('mqtt');
const { Client } = require('pg');
const http = require('http');

// Configurações
const MQTT_BROKER = process.env.MQTT_BROKER || 'hivemq';
const MQTT_PORT = process.env.MQTT_PORT || 1883;
const MQTT_TOPIC = process.env.MQTT_TOPIC || 'opaiot/temperature';

const DB_HOST = process.env.DB_HOST || 'postgres';
const DB_PORT = process.env.DB_PORT || 5432;
const DB_USER = process.env.DB_USER || 'iot_user';
const DB_PASSWORD = process.env.DB_PASSWORD || 'iot_password';
const DB_NAME = process.env.DB_NAME || 'iot_database';

let pgClient;

// ========================================
// Inicializar conexão PostgreSQL
// ========================================
async function initializeDatabase() {
    pgClient = new Client({
        user: DB_USER,
        password: DB_PASSWORD,
        host: DB_HOST,
        port: DB_PORT,
        database: DB_NAME,
    });

    try {
        await pgClient.connect();
        console.log('✓ Conectado ao PostgreSQL com TimescaleDB');
    } catch (err) {
        console.error('✗ Erro ao conectar ao PostgreSQL:', err.message);
        setTimeout(initializeDatabase, 5000); // Tenta reconectar a cada 5s
    }
}

// ========================================
// Inicializar conexão MQTT
// ========================================
function initializeMQTT() {
    const mqttUri = `mqtt://${MQTT_BROKER}:${MQTT_PORT}`;
    console.log(`Conectando ao HiveMQ em ${mqttUri}...`);

    const client = mqtt.connect(mqttUri, {
        clientId: 'nodejs-backend-' + Math.random().toString(16).slice(2, 8),
        reconnectPeriod: 1000,
        will: {
            topic: 'backend/status',
            payload: 'offline',
            qos: 1,
            retain: true,
        },
    });

    client.on('connect', () => {
        console.log('✓ Conectado ao HiveMQ (MQTT)');

        // Publicar status online
        client.publish('backend/status', 'online', { qos: 1, retain: true });

        // Fazer subscribe no tópico de temperatura
        client.subscribe(MQTT_TOPIC, (err) => {
            if (!err) {
                console.log(`✓ Inscrito no tópico: ${MQTT_TOPIC}`);
            } else {
                console.error(`✗ Erro ao se inscrever no tópico: ${err.message}`);
            }
        });
    });

    client.on('message', async (topic, message) => {
        try {
            const payload = message.toString();
            console.log(`📨 Mensagem recebida em ${topic}: ${payload}`);

            // Tentar fazer parse do JSON
            let data;
            try {
                data = JSON.parse(payload);
            } catch (e) {
                // Se não for JSON, criar um objeto simples
                data = {
                    temperature: parseFloat(payload),
                    humidity: null,
                };
            }

            // Validar dados
            if (!data.temperature) {
                console.error('✗ Mensagem inválida - falta temperatura');
                return;
            }

            // Armazenar no banco de dados
            await saveToDatabase({
                temperature: data.temperature,
                humidity: data.humidity || null,
                deviceId: data.deviceId || 'esp32-dht22',
                location: data.location || 'sala',
                timestamp: new Date(),
            });

        } catch (error) {
            console.error('✗ Erro ao processar mensagem MQTT:', error.message);
        }
    });

    client.on('error', (err) => {
        console.error('✗ Erro MQTT:', err.message);
    });

    client.on('reconnect', () => {
        console.log('🔄 Tentando reconectar ao HiveMQ...');
    });

    return client;
}

// ========================================
// Salvar dados no TimescaleDB
// ========================================
async function saveToDatabase(data) {
    try {
        const query = `
      INSERT INTO temperature_metrics (device_id, temperature, humidity, location, time)
      VALUES ($1, $2, $3, $4, $5);
    `;

        const values = [
            data.deviceId,
            data.temperature,
            data.humidity,
            data.location,
            data.timestamp,
        ];

        await pgClient.query(query, values);
        console.log(`✓ Dados salvos no banco de dados`);
    } catch (error) {
        console.error('✗ Erro ao salvar no banco de dados:', error.message);
    }
}

// ========================================
// API HTTP para consultar dados
// ========================================
function startHttpServer() {
    const server = http.createServer(async (req, res) => {
        // Headers CORS
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
        res.setHeader('Content-Type', 'application/json');

        if (req.method === 'OPTIONS') {
            res.writeHead(200);
            res.end();
            return;
        }

        try {
            if (req.url === '/health') {
                res.writeHead(200);
                res.end(JSON.stringify({ status: 'online' }));
            } else if (req.url === '/api/latest') {
                // Retorna o último registro de temperatura
                const result = await pgClient.query(`
          SELECT * FROM temperature_metrics 
          ORDER BY time DESC 
          LIMIT 1;
        `);

                res.writeHead(200);
                res.end(JSON.stringify(result.rows[0] || {}));
            } else if (req.url.startsWith('/api/data')) {
                // Retorna dados dos últimos períodos
                const hours = req.url.split('hours=')[1] || '24';
                const result = await pgClient.query(`
          SELECT * FROM temperature_metrics 
          WHERE time > NOW() - INTERVAL '${parseInt(hours)} hours'
          ORDER BY time DESC;
        `);

                res.writeHead(200);
                res.end(JSON.stringify(result.rows));
            } else if (req.url === '/api/status') {
                res.writeHead(200);
                res.end(JSON.stringify({
                    status: 'running',
                    mqtt_broker: MQTT_BROKER,
                    mqtt_topic: MQTT_TOPIC,
                    database: DB_NAME,
                }));
            } else {
                res.writeHead(404);
                res.end(JSON.stringify({ error: 'Endpoint não encontrado' }));
            }
        } catch (error) {
            console.error('✗ Erro na API HTTP:', error.message);
            res.writeHead(500);
            res.end(JSON.stringify({ error: error.message }));
        }
    });

    server.listen(3000, () => {
        console.log('✓ Servidor HTTP iniciado na porta 3000');
        console.log('  - GET /health - Status do servidor');
        console.log('  - GET /api/latest - Último registro');
        console.log('  - GET /api/data?hours=24 - Dados dos últimos N horas');
        console.log('  - GET /api/status - Status da conexão');
    });
}

// ========================================
// Inicializar aplicação
// ========================================
async function main() {
    console.log('\n╔════════════════════════════════════════╗');
    console.log('║   IoT Backend - Temperature Monitor   ║');
    console.log('╚════════════════════════════════════════╝\n');

    // Inicializar banco de dados
    await initializeDatabase();

    // Aguardar um pouco para garantir conexão
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Inicializar MQTT
    initializeMQTT();

    // Inicializar servidor HTTP
    startHttpServer();

    console.log('\n✓ Sistema iniciado com sucesso!\n');
}

// Tratamento de sinais de encerramento
process.on('SIGINT', async () => {
    console.log('\n🛑 Encerrando aplicação...');
    if (pgClient) {
        await pgClient.end();
    }
    process.exit(0);
});

// Iniciar tudo
main().catch(console.error);
