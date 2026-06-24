# 6. Consciencia

## Responsabilidade

Consolidar conhecimento das demais camadas, acompanhar o sistema ao longo do tempo
e apoiar decisoes de governanca, adaptacao e melhoria continua.

## Entradas

Registry, tracking, manifestos, documentos, previsoes, feedback humano, metricas de
monitoramento e trilha de auditoria.

## Saidas

- alertas e recomendacoes de investigacao;
- model card, datasheet e relatorio de rastreabilidade;
- conhecimento consultavel no dashboard;
- respostas conversacionais baseadas em fontes controladas;
- evidencias para aprovacao, retirada, rollback ou novo experimento.

## Componentes

- `monitoring/`: drift, previsoes e feedback;
- `governance/`: documentacao viva e criterios de uso responsavel;
- `knowledge/`: consolidacao das fontes controladas;
- `assistant/`: interface conversacional opcional com a API da OpenAI;
- `audit.py`: registro de eventos e responsabilidades.

## Limite conceitual

A Consciencia nao executa automaticamente retreinamento, rollback ou intervencao
fisica. Ela organiza evidencias e apoia uma decisao governada, com supervisao humana.
