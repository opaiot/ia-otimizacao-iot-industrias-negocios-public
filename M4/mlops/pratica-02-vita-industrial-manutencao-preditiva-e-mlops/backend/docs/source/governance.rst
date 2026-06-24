Governança e transparência
==========================

Model Card
----------

Documenta identificação, finalidade, métricas, dados, limitações, usos não recomendados, monitoramento e rollback.

Datasheet
---------

Documenta origem, composição, processamento, dados sensíveis, limitações e manutenção do dataset.

Rastreabilidade
---------------

O relatório conecta modelo, versão, run, dataset, hash, feature set, commit, dependências, limiar e documentos.

Responsabilidade
----------------

A predição apoia inspeções, mas não substitui especialistas nem autoriza controle físico automático.

Documentos operacionais
-----------------------

O diretório ``docs/governance`` também contém plano de versionamento, protocolo de experimentos, plano de monitoramento, matriz de responsabilidades e procedimento de incidente e rollback. Documentação não é uma etapa final: ela nasce com o desenvolvimento e muda quando dados, modelo ou uso mudam.

Assistente governado
--------------------

O assistente é uma interface da Consciência, não a fonte da verdade. Ele consulta registry, tracking, manifestos, relatórios, model card, datasheet, rastreabilidade e auditoria. Não aprova modelos nem executa ações.
