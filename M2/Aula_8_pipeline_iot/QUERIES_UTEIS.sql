-- ========================================
-- QUERIES ÚTEIS - TimescaleDB
-- ========================================
-- 
-- Use estas queries para consultar e analisar
-- dados do seu pipeline IoT
--
-- Acesso: docker-compose exec postgres psql -U iot_user -d iot_database

-- ========================================
-- CONSULTAS BÁSICAS
-- ========================================

-- Ver últimos registros
SELECT * FROM temperature_metrics 
ORDER BY time DESC 
LIMIT 10;

-- Contar total de registros
SELECT COUNT(*) as total_registros FROM temperature_metrics;

-- Ver período coberto pelos dados
SELECT 
  MIN(time) as primeiro_registro,
  MAX(time) as ultimo_registro,
  MAX(time) - MIN(time) as duracao
FROM temperature_metrics;

-- ========================================
-- ÚLTIMOS VALORES
-- ========================================

-- Valor mais recente
SELECT * FROM v_latest_temperatures;

-- Valor mais recente de um dispositivo
SELECT * FROM temperature_metrics 
WHERE device_id = 'esp32-dht22'
ORDER BY time DESC 
LIMIT 1;

-- ========================================
-- ESTATÍSTICAS POR PERÍODO
-- ========================================

-- Estatísticas de hoje
SELECT 
  COUNT(*) as amostras,
  ROUND(AVG(temperature)::numeric, 2) as temp_media,
  MIN(temperature) as temp_minima,
  MAX(temperature) as temp_maxima,
  ROUND(STDDEV(temperature)::numeric, 2) as temp_desvio,
  ROUND(AVG(humidity)::numeric, 2) as umidade_media,
  MIN(humidity) as umidade_minima,
  MAX(humidity) as umidade_maxima
FROM temperature_metrics 
WHERE time > NOW() - INTERVAL '1 day';

-- Estatísticas de hoje por hora
SELECT 
  time_bucket('1 hour', time) as hora,
  COUNT(*) as amostras,
  ROUND(AVG(temperature)::numeric, 2) as temp_media,
  MIN(temperature) as temp_min,
  MAX(temperature) as temp_max,
  ROUND(AVG(humidity)::numeric, 2) as umidade_media
FROM temperature_metrics
WHERE time > NOW() - INTERVAL '1 day'
GROUP BY hora
ORDER BY hora DESC;

-- ========================================
-- VARIAÇÕES DE TEMPERATURA
-- ========================================

-- Registrar quando a temperatura mudou mais de 2°C
SELECT 
  time,
  device_id,
  temperature,
  LAG(temperature) OVER (PARTITION BY device_id ORDER BY time) as temp_anterior,
  ROUND((temperature - LAG(temperature) OVER (PARTITION BY device_id ORDER BY time))::numeric, 2) as variacao
FROM temperature_metrics
WHERE time > NOW() - INTERVAL '24 hours'
  AND ABS(temperature - LAG(temperature) OVER (PARTITION BY device_id ORDER BY time)) > 2
ORDER BY time DESC;

-- ========================================
-- DETECÇÃO DE ANOMALIAS
-- ========================================

-- Temperaturas acima de 30°C
SELECT 
  time,
  device_id,
  location,
  temperature,
  humidity
FROM temperature_metrics
WHERE temperature > 30
  AND time > NOW() - INTERVAL '7 days'
ORDER BY temperature DESC;

-- Temperaturas abaixo de 15°C
SELECT 
  time,
  device_id,
  location,
  temperature,
  humidity
FROM temperature_metrics
WHERE temperature < 15
  AND time > NOW() - INTERVAL '7 days'
ORDER BY temperature;

-- Umidade muito alta (> 80%)
SELECT 
  time,
  device_id,
  location,
  temperature,
  humidity
FROM temperature_metrics
WHERE humidity > 80
  AND time > NOW() - INTERVAL '7 days'
ORDER BY humidity DESC;

-- ========================================
-- COMPARAÇÕES POR DISPOSITIVO
-- ========================================

-- Comparar média por dispositivo (últimas 24h)
SELECT 
  device_id,
  location,
  COUNT(*) as amostras,
  ROUND(AVG(temperature)::numeric, 2) as temp_media,
  ROUND(MIN(temperature)::numeric, 2) as temp_min,
  ROUND(MAX(temperature)::numeric, 2) as temp_max,
  ROUND(AVG(humidity)::numeric, 2) as umidade_media
FROM temperature_metrics
WHERE time > NOW() - INTERVAL '24 hours'
GROUP BY device_id, location
ORDER BY temp_media DESC;

-- ========================================
-- ANÁLISE DE SÉRIE TEMPORAL
-- ========================================

-- Média móvel (média dos últimos 5 registros)
SELECT 
  time,
  temperature,
  ROUND(AVG(temperature) OVER (
    ORDER BY time 
    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
  )::numeric, 2) as temp_media_movel
FROM temperature_metrics
WHERE time > NOW() - INTERVAL '24 hours'
ORDER BY time DESC
LIMIT 100;

-- Percentil (25%, 50%, 75%)
SELECT 
  time_bucket('1 hour', time) as hora,
  ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY temperature)::numeric, 2) as p25,
  ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY temperature)::numeric, 2) as p50,
  ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY temperature)::numeric, 2) as p75
FROM temperature_metrics
WHERE time > NOW() - INTERVAL '7 days'
GROUP BY hora
ORDER BY hora DESC;

-- ========================================
-- INTERVALOS SEM DADOS (GAPS)
-- ========================================

-- Detectar períodos onde não há dados (>5 minutos sem registros)
WITH time_gaps AS (
  SELECT 
    time,
    LAG(time) OVER (ORDER BY time) as time_anterior,
    EXTRACT(EPOCH FROM (time - LAG(time) OVER (ORDER BY time)))/60 as minutos_gap
  FROM temperature_metrics
  WHERE time > NOW() - INTERVAL '7 days'
)
SELECT 
  time_anterior as inicio_gap,
  time as fim_gap,
  ROUND(minutos_gap::numeric, 2) as minutos_sem_dados
FROM time_gaps
WHERE minutos_gap > 5
ORDER BY minutos_gap DESC;

-- ========================================
-- EXPORTAR DADOS
-- ========================================

-- Exportar como CSV (últimos 7 dias)
COPY (
  SELECT 
    time,
    device_id,
    location,
    ROUND(temperature::numeric, 2) as temperatura,
    ROUND(humidity::numeric, 2) as umidade
  FROM temperature_metrics
  WHERE time > NOW() - INTERVAL '7 days'
  ORDER BY time DESC
) TO STDOUT WITH CSV HEADER;

-- ========================================
-- ANÁLISE DE COMPRESSÃO
-- ========================================

-- Ver tamanho da tabela
SELECT * FROM hypertable_detailed_size('temperature_metrics');

-- Ver estatísticas das hypertables
SELECT 
  hypertable_name,
  owner,
  num_dimensions,
  num_hypertables
FROM timescaledb_information.hypertables;

-- Ver chunks (divisões da tabela por tempo)
SELECT 
  chunk_name,
  table_name,
  status,
  is_compressed
FROM timescaledb_information.chunks
WHERE hypertable_name = 'temperature_metrics'
ORDER BY range_start DESC;

-- ========================================
-- LIMPEZA E MANUTENÇÃO
-- ========================================

-- Remover registros com mais de 30 dias (já feito automaticamente)
-- DELETE FROM temperature_metrics 
-- WHERE time < NOW() - INTERVAL '30 days';

-- Reindex manual (se necessário)
-- REINDEX TABLE temperature_metrics;

-- Vacuum (limpeza de espaço)
-- VACUUM temperature_metrics;

-- ========================================
-- VIEWS PRÉ-DEFINIDAS
-- ========================================

-- Últimos valores por dispositivo
SELECT * FROM v_latest_temperatures;

-- Média horária
SELECT * FROM v_hourly_average
WHERE hour > NOW() - INTERVAL '24 hours'
ORDER BY hour DESC;

-- ========================================
-- QUERIES PARA O GRAFANA
-- ========================================

-- Série temporal - temperatura (formato para Grafana)
SELECT 
  $__time(time),
  temperature,
  device_id as metric
FROM temperature_metrics
WHERE time > $__timeFrom() AND time < $__timeTo()
ORDER BY time DESC;

-- Série temporal - umidade (formato para Grafana)
SELECT 
  $__time(time),
  humidity,
  device_id as metric
FROM temperature_metrics
WHERE time > $__timeFrom() AND time < $__timeTo()
AND humidity IS NOT NULL
ORDER BY time DESC;

-- Valor único - temperatura atual
SELECT temperature 
FROM temperature_metrics 
ORDER BY time DESC 
LIMIT 1;

-- Valor único - umidade atual
SELECT humidity 
FROM temperature_metrics 
ORDER BY time DESC 
LIMIT 1;

-- ========================================
-- TROUBLESHOOTING
-- ========================================

-- Verificar se a tabela existe
SELECT * FROM information_schema.tables 
WHERE table_name = 'temperature_metrics';

-- Listar todas as tabelas
\dt

-- Ver estrutura da tabela
\d temperature_metrics

-- Ver índices
SELECT * FROM pg_stat_user_indexes 
WHERE relname = 'temperature_metrics';

-- Ver tamanho total do banco
SELECT 
  pg_size_pretty(pg_database_size(current_database())) as tamanho_total;

-- Ver tamanho de cada tabela
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as tamanho
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ========================================
-- DICAS ÚTEIS
-- ========================================

-- \q                    - Sair do psql
-- \d                    - Listar tabelas
-- \d table_name         - Ver estrutura de uma tabela
-- SELECT version();     - Ver versão do PostgreSQL/TimescaleDB
-- \x                    - Toggle expanded output (melhor para muitas colunas)
-- \copy ... TO ...      - Exportar para arquivo local

-- Para queries que retornam muitas colunas, use:
-- \x on
-- SELECT * FROM temperature_metrics LIMIT 1;
-- \x off

