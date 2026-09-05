-- Criar extensão TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ========================================
-- Criar tabela de métricas de temperatura
-- ========================================
CREATE TABLE IF NOT EXISTS temperature_metrics (
  -- Identificador único
  id BIGSERIAL,
  
  -- Informações do dispositivo
  device_id VARCHAR(255) NOT NULL,
  location VARCHAR(255) NOT NULL DEFAULT 'sala',
  
  -- Dados sensoriais
  temperature FLOAT8 NOT NULL,
  humidity FLOAT8,
  
  -- Timestamp (coluna TIME - obrigatória para hypertable)
  time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- TimescaleDB exige que chaves únicas incluam a coluna de partição
  PRIMARY KEY (id, time)
);

-- ========================================
-- Converter em hypertable (série temporal)
-- ========================================
-- Isso otimiza a tabela para consultas de séries temporais
SELECT create_hypertable(
  'temperature_metrics',
  'time',
  if_not_exists => TRUE
);

-- ========================================
-- Criar índices para melhor performance
-- ========================================
CREATE INDEX IF NOT EXISTS idx_temperature_metrics_device_time 
ON temperature_metrics (device_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_temperature_metrics_location_time 
ON temperature_metrics (location, time DESC);

CREATE INDEX IF NOT EXISTS idx_temperature_metrics_time 
ON temperature_metrics (time DESC);

-- ========================================
-- Criar políticas de compressão automática
-- ========================================
-- Comprime dados com mais de 1 hora
ALTER TABLE temperature_metrics SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'device_id,location',
  timescaledb.compress_orderby = 'time DESC'
);

-- Políticas de compressão automática
SELECT add_compression_policy(
  'temperature_metrics',
  INTERVAL '1 hour',
  if_not_exists => TRUE
);

-- ========================================
-- Criar políticas de retenção
-- ========================================
-- Manter dados por 30 dias
SELECT add_retention_policy(
  'temperature_metrics',
  INTERVAL '30 days',
  if_not_exists => TRUE
);

-- ========================================
-- Criar views úteis
-- ========================================

-- View: Últimos valores por dispositivo
CREATE OR REPLACE VIEW v_latest_temperatures AS
SELECT DISTINCT ON (device_id)
  device_id,
  location,
  temperature,
  humidity,
  time
FROM temperature_metrics
ORDER BY device_id, time DESC;

-- View: Média horária por dispositivo
CREATE OR REPLACE VIEW v_hourly_average AS
SELECT
  device_id,
  location,
  time_bucket('1 hour', time) AS hour,
  AVG(temperature) AS avg_temperature,
  MIN(temperature) AS min_temperature,
  MAX(temperature) AS max_temperature,
  AVG(humidity) AS avg_humidity,
  COUNT(*) AS data_points
FROM temperature_metrics
GROUP BY device_id, location, hour
ORDER BY hour DESC;

-- ========================================
-- Dados de exemplo (opcional)
-- ========================================
-- Descomente para popular com dados de teste
/*
INSERT INTO temperature_metrics (device_id, location, temperature, humidity, time)
VALUES
  ('esp32-dht22', 'sala', 25.5, 60.0, NOW()),
  ('esp32-dht22', 'sala', 25.3, 59.5, NOW() - INTERVAL '1 minute'),
  ('esp32-dht22', 'sala', 25.1, 58.0, NOW() - INTERVAL '2 minutes');
*/

-- ========================================
-- Criar role de leitura para Grafana
-- ========================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'grafana_reader') THEN
    CREATE USER grafana_reader WITH PASSWORD 'grafana_password';
  ELSE
    ALTER USER grafana_reader WITH PASSWORD 'grafana_password';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE iot_database TO grafana_reader;
GRANT USAGE ON SCHEMA public TO grafana_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_reader;

-- Permitir select futuro em tabelas e views criadas no schema public
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO grafana_reader;

-- ========================================
-- Listar tabelas criadas
-- ========================================
-- Execute isso para verificar:
-- SELECT * FROM hypertable_detailed_size('temperature_metrics');
-- SELECT * FROM timescaledb_information.hypertables;
