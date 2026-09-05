"""Expõe linhas do CSV de qualidade do ar como métricas Prometheus.

Para mudar o comportamento do script, edite as constantes logo abaixo.
"""

import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Não foi possível importar o pandas.\n"
        f"Python usado: {sys.executable}\n"
        "Instale com o mesmo Python que executa o script. Exemplos:\n"
        "  python -m pip install -r requirements.txt\n"
        "  py -3.12 -m pip install -r requirements.txt\n"
        f"Erro original: {exc}"
    ) from exc

try:
    from prometheus_client import Gauge, start_http_server
except ImportError as exc:
    raise SystemExit(
        "Não foi possível importar o prometheus-client.\n"
        f"Python usado: {sys.executable}\n"
        "Instale com o mesmo Python que executa o script. Exemplos:\n"
        "  python -m pip install -r requirements.txt\n"
        "  py -3.12 -m pip install -r requirements.txt\n"
        f"Erro original: {exc}"
    ) from exc


# Configurações principais da aula.
CSV_FILE = Path("../data/IoT_Indoor_Air_Quality_Dataset.csv")
PORT = 8000
INTERVAL_SECONDS = 5.0
DEFAULT_DEVICE_ID = "iaq-sensor-01"
DEFAULT_LOCATION = "indoor-lab"


def normalize_name(name: str) -> str:
    # Remove acentos, troca separadores por "_" e deixa o nome fácil de usar em métricas.
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text.strip().lower())
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "column"


def normalize_columns(columns: List[str]) -> List[str]:
    # Garante nomes únicos para as colunas depois da normalização.
    seen: Dict[str, int] = {}
    output: List[str] = []
    for original in columns:
        base = normalize_name(original)
        count = seen.get(base, 0)
        seen[base] = count + 1
        output.append(base if count == 0 else f"{base}_{count + 1}")
    return output


def infer_unit(column: str) -> str:
    # Heurística simples: tenta inferir a unidade a partir do nome da coluna.
    name = column.lower()
    if "temp" in name:
        return "celsius"
    if "humid" in name:
        return "percent"
    if "co2" in name:
        return "ppm"
    if "voc" in name:
        return "ppb"
    if "pm2_5" in name or "pm25" in name or "pm_2_5" in name:
        return "ug_m3"
    if "pm10" in name or "pm_10" in name:
        return "ug_m3"
    if "pressure" in name:
        return "hpa"
    return "unknown"


def is_measurement(column: str, series: pd.Series) -> bool:
    # Só exportamos como métrica as colunas que parecem leituras numéricas de sensor.
    name = column.lower()
    if any(token in name for token in ("timestamp", "datetime", "time", "date")):
        return False
    if any(token in name for token in ("device", "sensor", "location", "room", "site", "building")):
        return False
    if any(token in name for token in ("alert", "alarm", "event", "state", "status", "occupancy", "command", "cmd")):
        return False
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.notna().sum() > 0 and numeric.notna().mean() >= 0.6


def first_matching(columns: List[str], tokens: Tuple[str, ...]) -> Optional[str]:
    # Encontra uma coluna de contexto, como timestamp, sensor ou localização.
    for column in columns:
        if any(token in column for token in tokens):
            return column
    return None


def label_value(row: pd.Series, column: Optional[str], fallback: str) -> str:
    # Labels do Prometheus não devem ficar vazios; por isso usamos fallback.
    if column is None:
        return fallback
    value = row.get(column, fallback)
    if pd.isna(value) or str(value).strip() == "":
        return fallback
    return str(value)


def start_metrics_server(port: int) -> None:
    # Se esta porta estiver ocupada, o erro mais comum é "Address already in use".
    try:
        start_http_server(port)
    except OSError as exc:
        raise SystemExit(
            f"Não foi possível iniciar o servidor de métricas na porta {port}.\n"
            "Verifique se outro processo já está usando essa porta:\n"
            f"  ss -ltnp | grep ':{port}'\n"
            "Se a porta estiver ocupada, altere a constante PORT no topo deste arquivo.\n"
            "Dica: o Prometheus normalmente usa a porta 9090; este exportador deve usar outra porta, como 8000.\n"
            f"Erro original: {exc}"
        ) from exc


def main() -> None:
    if not CSV_FILE.exists():
        raise SystemExit(f"CSV não encontrado: {CSV_FILE}")

    # 1. Lê o CSV e normaliza os nomes das colunas para uso em código e labels.
    df = pd.read_csv(CSV_FILE)
    df.columns = normalize_columns(df.columns.astype(str).tolist())
    if df.empty:
        raise SystemExit(f"O CSV não tem linhas: {CSV_FILE}")

    # 2. Seleciona as colunas numéricas que serão publicadas como métricas.
    measurement_columns = [column for column in df.columns if is_measurement(column, df[column])]
    if not measurement_columns:
        raise SystemExit("Nenhuma coluna numérica de medição foi encontrada.")

    # 3. Procura colunas que ajudam a contextualizar a leitura.
    timestamp_col = first_matching(list(df.columns), ("timestamp", "datetime", "time", "date"))
    device_col = first_matching(list(df.columns), ("device", "sensor"))
    location_col = first_matching(list(df.columns), ("location", "room", "site", "building"))

    # 4. Calcula média e desvio padrão para marcar anomalias simples.
    numeric_df = df[measurement_columns].apply(pd.to_numeric, errors="coerce")
    baselines = {
        column: {
            "mean": float(numeric_df[column].mean()),
            "std": float(numeric_df[column].std() or 0.0),
        }
        for column in measurement_columns
    }

    # 5. Define as métricas Prometheus que ficarão disponíveis em /metrics.
    sensor_value = Gauge(
        "opaiot_iaq_sensor_value",
        "Current simulated indoor air quality sensor value",
        ["device_id", "location", "metric", "unit"],
    )
    anomaly_flag = Gauge(
        "opaiot_iaq_anomaly_flag",
        "Simple anomaly flag based on two standard deviations",
        ["device_id", "location", "metric"],
    )
    stream_index = Gauge("opaiot_iaq_stream_index", "Current row index in the CSV stream")
    dataset_rows = Gauge("opaiot_iaq_dataset_rows", "Total rows loaded from the CSV")
    active_metrics = Gauge("opaiot_iaq_active_metrics", "Number of measurement columns exported")

    # 6. Inicia o servidor HTTP local usado pelo Prometheus para coletar métricas.
    start_metrics_server(PORT)
    dataset_rows.set(len(df))
    active_metrics.set(len(measurement_columns))

    print(f"Serving /metrics on http://localhost:{PORT}/metrics")
    print(f"CSV: {CSV_FILE}")
    print(f"Metrics: {', '.join(measurement_columns)}")
    print("Mantenha este terminal aberto enquanto o Prometheus coleta as métricas.")
    print("Para encerrar, pressione Ctrl+C.")

    # 7. Percorre as linhas em loop, simulando uma transmissão contínua de sensores.
    row_index = 0
    try:
        while True:
            row = df.iloc[row_index]
            device_id = label_value(row, device_col, DEFAULT_DEVICE_ID)
            location = label_value(row, location_col, DEFAULT_LOCATION)
            timestamp = label_value(row, timestamp_col, "no-timestamp")

            for metric in measurement_columns:
                value = pd.to_numeric(pd.Series([row[metric]]), errors="coerce").iloc[0]
                if pd.isna(value):
                    continue
                value = float(value)
                sensor_value.labels(device_id, location, metric, infer_unit(metric)).set(value)

                mean = baselines[metric]["mean"]
                std = baselines[metric]["std"]
                is_anomaly = 1.0 if std > 0 and abs(value - mean) > 2 * std else 0.0
                anomaly_flag.labels(device_id, location, metric).set(is_anomaly)

            stream_index.set(row_index)
            print(f"row={row_index} timestamp={timestamp} device={device_id} location={location}", flush=True)

            row_index = (row_index + 1) % len(df)
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nExportador Prometheus encerrado pelo usuário.")


if __name__ == "__main__":
    main()
