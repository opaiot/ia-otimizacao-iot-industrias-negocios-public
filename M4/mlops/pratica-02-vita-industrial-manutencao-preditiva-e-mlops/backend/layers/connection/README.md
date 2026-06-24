# 1. Conexao

## Responsabilidade

Identificar, adquirir e validar dados vindos de sensores, ativos e sistemas industriais.

## Entradas

- leituras de temperatura, vibracao, corrente e carga;
- identificador da maquina, planta e instante;
- dados de manutencao.

## Saidas

- snapshot identificado e versionavel;
- resultado de validacao de schema, nulos e faixas plausiveis;
- hash do arquivo coletado.

## Evidencias de MLOps

Versao do dataset, schema, periodo, quantidade de registros, hash e origem. Essas
evidencias alimentam a datasheet e a linhagem do modelo.

## Retroalimentacao

A Consciencia pode apontar falha de sensor, mudanca de distribuicao ou cobertura
insuficiente, solicitando investigacao nesta camada.
