API
===

Operação
--------

``GET /health`` verifica o serviço.

Arquitetura
-----------

``GET /api/v1/architecture`` apresenta o mapeamento das seis camadas.

Treino e registry
-----------------

* ``POST /api/v1/train``;
* ``GET /api/v1/experiments``;
* ``GET /api/v1/registry``;
* ``GET /api/v1/registry/production``.

Inferência e feedback
---------------------

* ``POST /api/v1/predict``;
* ``POST /api/v1/feedback``.

Monitoramento
-------------

``POST /api/v1/monitor`` gera dados de produção e calcula PSI.

Governança
----------

* ``GET /api/v1/governance/model-card``;
* ``GET /api/v1/governance/datasheet``;
* ``GET /api/v1/governance/traceability``;
* ``GET /api/v1/governance/audit``.

Consciência e assistente
------------------------

* ``GET /api/v1/consciousness/knowledge`` consolida fontes controladas;
* ``POST /api/v1/consciousness/assistant`` responde perguntas sobre essas evidências.

Sem ``OPENAI_API_KEY``, o endpoint usa um fallback local determinístico. Com a chave, usa a Responses API, mas continua limitado ao contexto governado fornecido pela VITA.

O contrato completo e os exemplos ficam disponíveis no Swagger em ``/docs``.
