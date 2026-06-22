from pathlib import Path

from fastapi.testclient import TestClient

from servico_patio import app


client = TestClient(app)
PASTA_IMAGENS = Path(__file__).parent / "images" / "patio"


def test_health_confirma_modelo_carregado():
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "modelo": "yolov8n.pt"}


def test_predict_retorna_resumo_operacional():
    caminho = PASTA_IMAGENS / "patio_estacionamento.jpg"

    with caminho.open("rb") as imagem:
        resposta = client.post(
            "/predict",
            params={"confianca_minima": 0.35},
            files={"arquivo": (caminho.name, imagem, "image/jpeg")},
        )

    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["arquivo"] == caminho.name
    assert corpo["modelo"] == "yolov8n.pt"
    assert corpo["total"] > 0
    assert corpo["contagens"]["carro"] > 0
    assert len(corpo["deteccoes"]) == corpo["total"]


def test_predict_rejeita_arquivo_que_nao_e_imagem():
    resposta = client.post(
        "/predict",
        files={"arquivo": ("dados.txt", b"nao e uma imagem", "text/plain")},
    )

    assert resposta.status_code == 415
    assert "Formato não suportado" in resposta.json()["detail"]
