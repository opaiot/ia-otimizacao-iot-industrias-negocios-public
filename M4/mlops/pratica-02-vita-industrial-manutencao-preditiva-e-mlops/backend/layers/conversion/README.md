# 2. Conversao

## Responsabilidade

Converter dados brutos em informacao consistente e reutilizavel por treino e inferencia.

## Entradas

Snapshot validado pela Conexao.

## Saidas

- dados preparados;
- features derivadas;
- definicoes e versao do feature set.

## Evidencias de MLOps

Regras de transformacao, versao das features e contrato compartilhado entre treino
e producao. No case, esse registro funciona como uma feature store didatica.

## Retroalimentacao

Drift, falha de qualidade ou inconsistencia treino-producao podem exigir revisao das
regras, sem sobrescrever silenciosamente a versao anterior.
