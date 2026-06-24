"""Gera documentos vivos de transparencia ligados as evidencias do treino."""

from pathlib import Path

from backend.config import DATASHEET_PATH, MODEL_CARD_PATH, TRACEABILITY_PATH


def generate_governance_documents(registered: dict, manifest: dict) -> dict:
    metrics = registered["metrics"]
    data = registered["data_version"]
    model_card = f"""# Model Card - PumpFailureRisk {registered['version']}

## Identificacao e responsabilidade

- Modelo registrado: `PumpFailureRisk`
- Versao e estagio: `{registered['version']}` / `{registered['stage']}`
- Algoritmo: `{registered['algorithm']}`
- Responsavel: {registered['owner']}
- Run de origem: `{registered['source_run_id']}`
- Commit do codigo: `{registered['code_commit']}`
- Hash do modelo: `{registered['model_sha256']}`
- Aprovacao: `{registered['approval']['status']}`
- Revisao humana obrigatoria: `{registered['approval']['human_review_required']}`

## Finalidade e decisao apoiada

Estimar o risco de falha de bombas e motores nos proximos sete dias para priorizar
inspecoes. O modelo apoia a equipe de manutencao; ele nao controla o equipamento.

## Uso esperado

- triagem e priorizacao de ativos para inspecao;
- acompanhamento de risco em painel operacional;
- investigacao conjunta com sinais fisicos e parecer humano.

## Usos não recomendados

- desligamento automatico de equipamento;
- substituicao da avaliacao de especialistas;
- uso em outra planta, ativo ou sensor sem nova validacao;
- decisao de seguranca baseada apenas na probabilidade;
- avaliacao de pessoas, equipes ou fornecedores.

## Dados, features e linhagem

- Dataset: `{data['name']}`
- SHA-256: `{data['sha256']}`
- Schema: `{data['schema_version']}`
- Feature set: `{registered['feature_set_version']}`
- Limiar: `{registered['decision_threshold']}`
- Datasheet vinculada: `docs/governance/datasheet.md`

## Metricas de validacao

- ROC AUC: {metrics['roc_auc']:.4f}
- F1: {metrics['f1']:.4f}
- Precisao para falha: {metrics['precision_failure']:.4f}
- Recall para falha: {metrics['recall_failure']:.4f}
- Custo esperado: {metrics['expected_cost']:.4f}

## Limites, riscos e explicabilidade

- os dados sao sinteticos e nao demonstram desempenho em uma planta real;
- metricas por planta e por tipo de ativo ainda nao foram validadas;
- falsos negativos possuem custo operacional maior que falsos positivos;
- mudancas de sensor, processo ou manutencao podem degradar o modelo;
- a probabilidade representa risco estimado, nao uma causa comprovada;
- a recomendacao deve ser confrontada com alertas fisicos e conhecimento tecnico.

## Monitoramento e criterios de revisao

- investigar PSI maior ou igual a `0.20`;
- acompanhar recall, falsos negativos, falsos alarmes e feedback humano;
- revisar apos drift, incidente, mudanca de sensor ou de processo;
- drift inicia investigacao e nao autoriza retreinamento automatico.

## Aprovacao, retirada e rollback

A promocao exige dados identificados, validacao, run rastreavel, artefato carregavel,
documentacao e aprovacao humana. Em degradacao confirmada, a equipe registra o
incidente, retira a versao e restaura a ultima versao aprovada.
"""

    datasheet = f"""# Datasheet - {data['name']}

## Motivacao e uso

Base didatica para representar leituras agregadas de sensores IoT de bombas e
motores. Foi criada exclusivamente para ensino de MLOps e Arquitetura 6C.

## Identificacao e versao

- Nome: `{data['name']}`
- Schema: `{data['schema_version']}`
- Linhas: {data['rows']}
- SHA-256: `{data['sha256']}`
- Caminho: `{data['path']}`
- Geracao: `{manifest['created_at']}`
- Semente: `{manifest['random_seed']}`

## Origem e coleta

Dados sinteticos gerados por distribuicoes controladas, sem empresa, equipamento ou
trabalhador real. As leituras representam uma janela agregada de 24 horas.

## Composicao e rotulo

- identificacao da maquina, planta e instante;
- idade do motor, temperatura, vibracao, corrente e carga;
- manutencao recente;
- rotulo sintetico de falha nos proximos sete dias.

## Preparacao, features e split

- validacao de schema, nulos e faixas plausiveis;
- interacao temperatura-carga e vibracao ajustada pela idade;
- feature set: `{registered['feature_set_version']}`;
- split estratificado: `{manifest['split']['test_size']:.0%}` para teste;
- semente do split: `{manifest['split']['seed']}`.

## Qualidade, cobertura e vieses conhecidos

- validacao: `{manifest['validation']['status']}`;
- nulos encontrados: `{manifest['validation']['null_values']}`;
- plantas simuladas: SP, MG e PR;
- as proporcoes e relacoes de risco foram definidas para fins didaticos;
- eventos raros, falhas de sensor e atrasos de comunicacao nao sao realistas;
- a cobertura nao sustenta generalizacao para fabricantes ou plantas reais.

## Dados pessoais e sensíveis, acesso e segurança

Nao ha dados pessoais. Em uso real, identificadores de ativos, localizacao e dados
operacionais exigiriam controle de acesso, retencao, classificacao e auditoria.

## Manutencao e versionamento

Cada snapshot deve receber nome, schema, hash, periodo e responsavel. Mudanca de
distribuicao deve gerar nova versao, atualizar esta datasheet e provocar avaliacao
do modelo vinculado. A base nao deve ser sobrescrita silenciosamente.
"""

    traceability = f"""# Relatorio de rastreabilidade

| Elemento | Evidencia |
| --- | --- |
| Modelo | PumpFailureRisk {registered['version']} |
| Run de origem | `{registered['source_run_id']}` |
| Algoritmo | {registered['algorithm']} |
| Dataset | `{data['name']}` |
| Hash dos dados | `{data['sha256']}` |
| Feature set | `{registered['feature_set_version']}` |
| Commit | `{registered['code_commit']}` |
| Hash das dependencias | `{manifest['requirements_sha256']}` |
| Hash do modelo | `{registered['model_sha256']}` |
| Split | estratificado, teste={manifest['split']['test_size']}, seed={manifest['split']['seed']} |
| Limiar | {registered['decision_threshold']} |
| Estagio | {registered['stage']} |
| Aprovacao | {registered['approval']['status']} |

Este relatorio conecta codigo, dados, configuracao, features, ambiente, execucao,
avaliacao, aprovacao e artefato implantado.
"""

    MODEL_CARD_PATH.write_text(model_card, encoding="utf-8")
    DATASHEET_PATH.write_text(datasheet, encoding="utf-8")
    TRACEABILITY_PATH.write_text(traceability, encoding="utf-8")
    return {
        "model_card": str(MODEL_CARD_PATH),
        "datasheet": str(DATASHEET_PATH),
        "traceability_report": str(TRACEABILITY_PATH),
    }


def read_document(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError("O documento ainda nao foi gerado. Execute o treinamento.")
    return path.read_text(encoding="utf-8")
