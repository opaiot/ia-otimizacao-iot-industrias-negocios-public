MLOps e rastreabilidade
=======================

Tracking
--------

Cada candidato gera uma run no MLflow e uma linha em ``runs.csv``. Parâmetros, métricas, manifesto, features e modelo são associados ao mesmo ``run_id``.

Registry
--------

``registry.json`` registra versões, estágio, métricas, artefato, hash do modelo, run e dados de origem. Uma nova promoção arquiva a versão anterior.

Versionamento
-------------

O manifesto registra:

* hash SHA-256 dos dados;
* versão do schema;
* versão das features;
* commit Git;
* hash das dependências;
* seed;
* estratégia e proporção do split;
* limiar;
* hash do modelo aprovado.

Monitoramento
-------------

O PSI compara features de produção com a referência de treino. PSI maior ou igual a 0,20 gera investigação. Drift não dispara retreinamento automático.

Transparência e responsabilidade
--------------------------------

Model card e datasheet são vinculadas ao registry, à run e ao manifesto. A trilha de auditoria registra promoção, inferência, monitoramento, feedback e uso do assistente. Sem essa ligação, os arquivos seriam documentação isolada, não evidência operacional.
