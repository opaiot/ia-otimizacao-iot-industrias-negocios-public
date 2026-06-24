Visão geral da Prática 2
========================

.. image:: ../images/pratica2_vita_manutencao_preditiva_mlops.png
   :align: center
   :width: 100%
   :alt: Infográfico da Prática 2 sobre manutenção preditiva, Arquitetura 6C e MLOps

O desafio
---------

Uma empresa monitora bombas e motores nas plantas de São Paulo, Minas Gerais e
Paraná. O sistema estima o risco de falha nos próximos sete dias, prioriza inspeções
e acompanha mudanças nos dados, sem executar automaticamente ações físicas críticas.

O que a prática conecta
-----------------------

* sensores IoT e dados versionados;
* curadoria e features compartilhadas entre treino e inferência;
* algoritmos, experimentos, modelos e registry;
* avaliação, diagnóstico e recomendação operacional;
* API e dashboard;
* monitoramento, feedback, governança e auditoria;
* assistente conversacional baseado em fontes controladas.

Leitura correta da arquitetura
------------------------------

A **Arquitetura 6C** é o framework de referência. A **VITA** é a plataforma que a
materializa neste projeto. As camadas são níveis funcionais que interagem de forma
bidirecional; elas não representam uma pipeline rígida. A camada de Consciência
consolida evidências e apoia decisões, mas não executa automaticamente retreinamento,
rollback ou intervenção física.

Resultado esperado
------------------

Ao final, o estudante deve conseguir reconstruir qual código, dataset, feature set,
execução e artefato produziram uma previsão; verificar a versão em produção; avaliar
drift; consultar a documentação de transparência; e compreender os limites de uso do
sistema.
