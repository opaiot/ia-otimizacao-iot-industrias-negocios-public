"""API para o case de monitoramento inteligente de pátio."""

from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from ultralytics import YOLO


NOME_MODELO = "yolov8n.pt"
EXTENSOES_PERMITIDAS = {".jpg", ".jpeg", ".png"}
CLASSES_DE_INTERESSE = {
    "person": "pessoa",
    "bicycle": "bicicleta",
    "car": "carro",
    "motorcycle": "motocicleta",
    "bus": "ônibus",
    "truck": "caminhão",
}


class Deteccao(BaseModel):
    classe: str
    confianca: float
    caixa_xyxy: list[float] = Field(
        description="Coordenadas [x1, y1, x2, y2] da caixa delimitadora."
    )


class RespostaPredicao(BaseModel):
    arquivo: str
    modelo: str
    confianca_minima: float
    contagens: dict[str, int]
    total: int
    status: str
    deteccoes: list[Deteccao]


app = FastAPI(
    title="Monitoramento Inteligente de Pátio",
    description=(
        "Serviço didático da Prática 1 do curso de IA, Otimização e IoT. "
        "Recebe uma imagem e identifica pessoas e veículos com YOLO."
    ),
    version="1.0.0",
)

# O modelo é carregado uma única vez durante a inicialização do processo.
modelo = YOLO(NOME_MODELO)


def gerar_status_operacional(contagens: dict[str, int]) -> str:
    pessoas = contagens.get("pessoa", 0)
    veiculos = sum(
        contagens.get(classe, 0)
        for classe in ["carro", "motocicleta", "ônibus", "caminhão"]
    )

    if pessoas > 0 and veiculos > 0:
        return "ATENÇÃO: pessoas e veículos identificados na mesma cena"
    if veiculos > 0:
        return "Movimentação de veículos identificada"
    if pessoas > 0:
        return "Movimentação de pessoas identificada"
    return "Nenhum objeto de interesse identificado"


def decodificar_imagem(conteudo: bytes) -> np.ndarray:
    dados = np.frombuffer(conteudo, dtype=np.uint8)
    imagem = cv2.imdecode(dados, cv2.IMREAD_COLOR)
    if imagem is None:
        raise HTTPException(status_code=400, detail="Não foi possível ler a imagem.")
    return imagem


def analisar_imagem(imagem: np.ndarray, confianca_minima: float) -> dict:
    resultado = modelo.predict(
        source=imagem,
        conf=confianca_minima,
        verbose=False,
    )[0]

    deteccoes = []
    for caixa in resultado.boxes:
        id_classe = int(caixa.cls.item())
        classe_original = resultado.names[id_classe]
        if classe_original not in CLASSES_DE_INTERESSE:
            continue

        deteccoes.append(
            {
                "classe": CLASSES_DE_INTERESSE[classe_original],
                "confianca": round(float(caixa.conf.item()), 3),
                "caixa_xyxy": [
                    round(valor, 1) for valor in caixa.xyxy[0].tolist()
                ],
            }
        )

    contagens = Counter(deteccao["classe"] for deteccao in deteccoes)
    return {
        "deteccoes": deteccoes,
        "contagens": dict(contagens),
        "total": len(deteccoes),
        "status": gerar_status_operacional(dict(contagens)),
    }


@app.get("/health", tags=["operacao"])
def verificar_saude() -> dict[str, str]:
    """Confirma que a API e o modelo foram carregados."""
    return {
        "status": "ok",
        "modelo": NOME_MODELO,
    }


@app.post("/predict", response_model=RespostaPredicao, tags=["inferencia"])
def realizar_predicao(
    confianca_minima: float = Query(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Limiar mínimo para aceitar uma detecção.",
    ),
    arquivo: UploadFile = File(..., description="Imagem JPG ou PNG do patio."),
) -> RespostaPredicao:
    """Recebe uma imagem e retorna pessoas e veículos identificados."""
    nome_arquivo = arquivo.filename or "imagem_sem_nome"
    extensao = Path(nome_arquivo).suffix.lower()
    if extensao not in EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status_code=415,
            detail="Formato não suportado. Envie uma imagem JPG ou PNG.",
        )

    conteudo = arquivo.file.read()
    if not conteudo:
        raise HTTPException(status_code=400, detail="O arquivo enviado está vazio.")

    imagem = decodificar_imagem(conteudo)
    analise = analisar_imagem(imagem, confianca_minima)

    return RespostaPredicao(
        arquivo=nome_arquivo,
        modelo=NOME_MODELO,
        confianca_minima=confianca_minima,
        **analise,
    )
