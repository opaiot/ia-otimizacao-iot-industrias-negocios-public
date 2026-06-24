# Datasheet - sensors_train_v1

## Motivacao e uso

Base didatica para representar leituras agregadas de sensores IoT de bombas e
motores. Foi criada exclusivamente para ensino de MLOps e Arquitetura 6C.

## Identificacao e versao

- Nome: `sensors_train_v1`
- Schema: `sensor_snapshot:v1`
- Linhas: 1200
- SHA-256: `3468017f15aceee2cd9fef4955eef9c6eeada1f8866e5991f52dcd581211c5f1`
- Caminho: `data/raw/sensors_train_v1.csv`
- Geracao: `2026-06-24T05:07:31.804404+00:00`
- Semente: `42`

## Origem e coleta

Dados sinteticos gerados por distribuicoes controladas, sem empresa, equipamento ou
trabalhador real. As leituras representam uma janela agregada de 24 horas.

## Composicao e rotulo

- identificacao da maquina, planta e instante;
- idade do motor, temperatura, vibracao, corrente e carga;
- manutencao recente;
- rotulo sintetico de falha nos proximos sete dias.

## Preparacao, features e split

- validacao de schema, nulos e faixas plausiveis;
- interacao temperatura-carga e vibracao ajustada pela idade;
- feature set: `industrial_sensor_features:v1`;
- split estratificado: `25%` para teste;
- semente do split: `42`.

## Qualidade, cobertura e vieses conhecidos

- validacao: `valid`;
- nulos encontrados: `0`;
- plantas simuladas: SP, MG e PR;
- as proporcoes e relacoes de risco foram definidas para fins didaticos;
- eventos raros, falhas de sensor e atrasos de comunicacao nao sao realistas;
- a cobertura nao sustenta generalizacao para fabricantes ou plantas reais.

## Dados pessoais e sensíveis, acesso e segurança

Nao ha dados pessoais. Em uso real, identificadores de ativos, localizacao e dados
operacionais exigiriam controle de acesso, retencao, classificacao e auditoria.

## Manutencao e versionamento

Cada snapshot deve receber nome, schema, hash, periodo e responsavel. Mudanca de
distribuicao deve gerar nova versao, atualizar esta datasheet e provocar avaliacao
do modelo vinculado. A base nao deve ser sobrescrita silenciosamente.
