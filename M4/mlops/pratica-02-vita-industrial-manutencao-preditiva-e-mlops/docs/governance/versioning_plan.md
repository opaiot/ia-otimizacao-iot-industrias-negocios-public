# Plano de versionamento e reprodutibilidade

## Unidade reproduzivel

Uma execucao e identificada pela combinacao de codigo, dados, configuracao, features,
dependencias, semente, split, algoritmo, metricas e artefato.

| Elemento | Identificacao no case | Evidencia |
| --- | --- | --- |
| Codigo | commit Git | `code_commit` |
| Dados | nome, schema e SHA-256 | manifesto e datasheet |
| Configuracao | seed, split e limiar | manifesto |
| Features | nome e versao | `feature_definitions.json` |
| Experimento | run id | MLflow e `runs.csv` |
| Modelo | versao, estagio e SHA-256 | registry |
| Ambiente | hash das dependencias | manifesto |

Arquivos com nomes como `modelo_final.pkl` nao sao considerados uma estrategia de
versionamento. Uma versao precisa ser conhecida, auditavel e recuperavel.
