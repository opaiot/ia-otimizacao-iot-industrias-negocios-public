# Plano de monitoramento

| Dimensao | Indicador | Criterio | Resposta |
| --- | --- | --- | --- |
| Dados | schema, nulos e faixas | qualquer violacao | bloquear lote e investigar |
| Drift | PSI por feature | PSI >= 0,20 | investigar mudanca |
| Modelo | recall de falhas | queda confirmada | revisar dados e modelo |
| Operacao | falsos alarmes | aumento persistente | revisar limiar e processo |
| Feedback | falhas confirmadas | divergencia recorrente | abrir analise de causa |
| Servico | disponibilidade e latencia | fora do SLO | acionar operacao |

Drift e um sinal, nao uma ordem de retreinamento. Qualquer mudanca exige diagnostico,
nova execucao rastreada, validacao, documentacao e aprovacao.
