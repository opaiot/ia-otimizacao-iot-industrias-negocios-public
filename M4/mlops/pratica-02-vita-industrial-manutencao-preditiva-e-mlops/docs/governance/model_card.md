# Model Card - PumpFailureRisk 1.0.5

## Identificacao e responsabilidade

- Modelo registrado: `PumpFailureRisk`
- Versao e estagio: `1.0.5` / `production`
- Algoritmo: `LogisticRegression`
- Responsavel: Equipe de IA e Manutencao
- Run de origem: `2398ade0587a4d0b85eea5f905f8af04`
- Commit do codigo: `e0558df6cce230f0338f3f0cd77ad308083899ec`
- Hash do modelo: `dffed19376552c3f3e5626b832fbad3f83864eb9b60b84da965fa444ea682d9f`
- Aprovacao: `approved_for_educational_use`
- Revisao humana obrigatoria: `True`

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

- Dataset: `sensors_train_v1`
- SHA-256: `3468017f15aceee2cd9fef4955eef9c6eeada1f8866e5991f52dcd581211c5f1`
- Schema: `sensor_snapshot:v1`
- Feature set: `industrial_sensor_features:v1`
- Limiar: `0.35`
- Datasheet vinculada: `docs/governance/datasheet.md`

## Metricas de validacao

- ROC AUC: 0.7827
- F1: 0.4162
- Precisao para falha: 0.2808
- Recall para falha: 0.8039
- Custo esperado: 0.6833

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
