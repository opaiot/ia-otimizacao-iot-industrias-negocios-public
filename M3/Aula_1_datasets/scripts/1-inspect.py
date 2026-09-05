"""Inspeciona um CSV de qualidade do ar e gera artefatos didáticos.

Para mudar o comportamento do script, edite as constantes logo abaixo.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Configurações principais da aula.
CSV_FILE = PROJECT_ROOT / "data" / "IoT_Indoor_Air_Quality_Dataset.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
MAX_EVENTS = 500


def normalize_name(name: str) -> str:
    # Remove acentos, troca separadores por "_" e deixa o nome fácil de usar em código.
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text.strip().lower())
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "column"


def normalize_columns(columns: List[str]) -> Tuple[List[str], Dict[str, str]]:
    # Gera nomes normalizados e guarda o mapa entre nome original e nome novo.
    seen: Dict[str, int] = {}
    normalized: List[str] = []
    mapping: Dict[str, str] = {}
    for original in columns:
        base = normalize_name(original)
        count = seen.get(base, 0)
        seen[base] = count + 1
        name = base if count == 0 else f"{base}_{count + 1}"
        normalized.append(name)
        mapping[str(original)] = name
    return normalized, mapping



def is_numeric_series(series: pd.Series) -> bool:
    # Consideramos numérica uma coluna em que pelo menos 60% dos valores viram número.
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.notna().sum() > 0 and numeric.notna().mean() >= 0.6


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
    if "pressure" in name or "pressao" in name:
        return "hpa"
    return "unknown"


def classify_column(column: str, series: pd.Series) -> Tuple[str, str, str]:
    # Classifica a coluna em uma categoria semântica usada no exercício de IoT.
    name = column.lower()
    unit = infer_unit(name)

    if any(token in name for token in ("timestamp", "datetime", "date_time", "time", "date")):
        return "metadata", "time reference for each observation", unit
    if any(token in name for token in ("alert", "alarm", "event", "anomaly")):
        return "event", "discrete occurrence or warning", unit
    if any(token in name for token in ("state", "status", "online", "occupancy", "occupied")):
        return "state", "current condition of sensor or environment", unit
    if any(token in name for token in ("device", "sensor", "location", "room", "site", "building")):
        return "metadata", "context that identifies origin or place", unit
    if any(token in name for token in ("command", "cmd", "set_", "actuator", "control")):
        return "command", "action requested to an actuator or system", unit
    if is_numeric_series(series):
        return "measurement", "numeric value observed by a sensor", unit
    return "metadata", "descriptive or categorical context", unit


def sample_values(series: pd.Series, limit: int = 4) -> str:
    # Mostra poucos exemplos para o relatório ficar legível.
    values = []
    for value in series.dropna().astype(str).unique().tolist():
        values.append(value)
        if len(values) >= limit:
            break
    return "; ".join(values)


def json_value(value: Any) -> Any:
    # Converte valores do pandas/numpy para tipos que o json consegue gravar.
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    return value


def first_matching(columns: List[str], tokens: Tuple[str, ...]) -> Optional[str]:
    # Encontra a primeira coluna cujo nome contém algum dos termos esperados.
    for column in columns:
        if any(token in column for token in tokens):
            return column
    return None


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    # ensure_ascii=False mantém acentos legíveis nos arquivos JSON.
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_outputs(csv_path: Path, out_dir: Path, max_events: int) -> None:
    # 1. Prepara a pasta onde os arquivos de saída serão gravados.
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Lê o CSV original e cria uma cópia com nomes de colunas normalizados.
    raw_df = pd.read_csv(csv_path)
    normalized_columns, mapping = normalize_columns(raw_df.columns.astype(str).tolist())
    df = raw_df.copy()
    df.columns = normalized_columns

    profiles: List[Dict[str, Any]] = []
    classifications: List[Dict[str, Any]] = []
    measurement_columns: List[str] = []

    reverse_mapping = {normalized: original for original, normalized in mapping.items()}
    for column in df.columns:
        # 3. Para cada coluna, criamos um perfil técnico e uma classificação semântica.
        semantic_class, reason, unit = classify_column(column, df[column])
        if semantic_class == "measurement":
            measurement_columns.append(column)
        profiles.append(
            {
                "original_name": reverse_mapping.get(column, column),
                "normalized_name": column,
                "dtype": str(df[column].dtype),
                "non_null": int(df[column].notna().sum()),
                "null_count": int(df[column].isna().sum()),
                "unique_values": int(df[column].nunique(dropna=True)),
                "sample_values": sample_values(df[column]),
            }
        )
        classifications.append(
            {
                "column": column,
                "semantic_class": semantic_class,
                "unit": unit,
                "reason": reason,
                "prometheus_metric": "opaiot_iaq_sensor_value" if semantic_class == "measurement" else "",
            }
        )

    pd.DataFrame(profiles).to_csv(out_dir / "columns_profile.csv", index=False)
    pd.DataFrame(classifications).to_csv(out_dir / "semantic_classification.csv", index=False)

    # 4. Gera uma estatística descritiva para as colunas numéricas.
    numeric_df = df.apply(pd.to_numeric, errors="coerce")
    numeric_columns = [column for column in df.columns if numeric_df[column].notna().sum() > 0]
    if numeric_columns:
        summary = numeric_df[numeric_columns].describe().transpose().reset_index()
        summary = summary.rename(columns={"index": "column"})
        summary["missing"] = [int(df[column].isna().sum()) for column in summary["column"]]
        summary.to_csv(out_dir / "numeric_summary.csv", index=False)
    else:
        pd.DataFrame(columns=["column", "count", "mean", "std", "min", "25%", "50%", "75%", "max", "missing"]).to_csv(
            out_dir / "numeric_summary.csv", index=False
        )

    # 5. Cria um esquema mínimo para representar leituras IoT como eventos.
    schema = {
        "name": "opaiot_iot_event_minimal_schema",
        "version": "1.0",
        "required_fields": {
            "event_id": "string",
            "timestamp": "string",
            "device_id": "string",
            "location": "string",
            "type": "measurement | event | state | command | metadata",
            "metric": "string",
            "value": "number | string",
            "unit": "string",
            "source_dataset": "string",
        },
    }
    write_json(out_dir / "iot_event_schema.json", schema)

    timestamp_col = first_matching(list(df.columns), ("timestamp", "datetime", "time", "date"))
    device_col = first_matching(list(df.columns), ("device", "sensor"))
    location_col = first_matching(list(df.columns), ("location", "room", "site", "building"))

    # 6. Converte cada medida em uma linha JSONL, formato comum em pipelines de dados.
    events_path = out_dir / "normalized_events.jsonl"
    event_count = 0
    with events_path.open("w", encoding="utf-8") as handle:
        for row_index, row in df.iterrows():
            for metric in measurement_columns:
                if event_count >= max_events:
                    break
                value = pd.to_numeric(pd.Series([row[metric]]), errors="coerce").iloc[0]
                if pd.isna(value):
                    continue
                event = {
                    "event_id": f"evt-{row_index + 1:05d}-{metric}",
                    "timestamp": str(json_value(row[timestamp_col])) if timestamp_col else "",
                    "device_id": str(json_value(row[device_col])) if device_col else "iaq-sensor-unknown",
                    "location": str(json_value(row[location_col])) if location_col else "unknown",
                    "type": "measurement",
                    "metric": metric,
                    "value": float(value),
                    "unit": infer_unit(metric),
                    "source_dataset": csv_path.name,
                }
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
                event_count += 1
            if event_count >= max_events:
                break

    # 7. Resume a execução para facilitar a conferência dos resultados.
    summary_payload = {
        "csv_file": csv_path.as_posix(),
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_mapping": mapping,
        "measurement_columns": measurement_columns,
        "event_records_written": event_count,
        "outputs": [
            "columns_profile.csv",
            "semantic_classification.csv",
            "numeric_summary.csv",
            "normalized_events.jsonl",
            "iot_event_schema.json",
        ],
    }
    write_json(out_dir / "inspection_summary.json", summary_payload)

    print(f"CSV: {csv_path.as_posix()}")
    print(f"Rows: {len(df)} | Columns: {len(df.columns)}")
    print(f"Measurement columns: {', '.join(measurement_columns) or 'none'}")
    print(f"Outputs written to: {out_dir}")


def main() -> None:
    build_outputs(CSV_FILE, OUTPUT_DIR, MAX_EVENTS)


if __name__ == "__main__":
    main()
