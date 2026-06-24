Fluxo de dados e decisão
========================

.. code-block:: text

   sensores IoT
      -> validação
      -> features
      -> estado digital do ativo
      -> risco de falha
      -> prioridade de manutenção
      -> monitoramento e feedback

Treino
------

O treino gera snapshot de dados, manifesto, três runs, modelos candidatos, versão aprovada e documentos de governança.

Inferência
----------

A mesma função de features usada no treino transforma a leitura recebida. A resposta informa versão do modelo e run de origem.

Feedback
--------

O resultado real pode ser enviado a ``POST /api/v1/feedback``. Essa evidência fecha o ciclo entre decisão e aprendizado.
