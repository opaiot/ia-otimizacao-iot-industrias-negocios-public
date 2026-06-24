Modelos e seleção
=================

Os algoritmos ficam em ``backend/layers/cyber_physical/algorithms/`` porque a modelagem e a representação preditiva do ativo pertencem à camada Ciberfísica. A Cognição avalia e interpreta os resultados.

Candidatos
----------

* Regressão Logística;
* Random Forest;
* Gradient Boosting.

Todos utilizam o mesmo split, features, seed e limiar.

Métricas
--------

São registrados ROC AUC, F1, precisão, recall, falsos positivos, falsos negativos e custo esperado.

Critério de promoção
--------------------

Falsos negativos recebem custo maior. O candidato com menor custo esperado é priorizado; o recall é usado como critério de desempate. A regra é didática e deve ser definida com especialistas em um sistema real.
