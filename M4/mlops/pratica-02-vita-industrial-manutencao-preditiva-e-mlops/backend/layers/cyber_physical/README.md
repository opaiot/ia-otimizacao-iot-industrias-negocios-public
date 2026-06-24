# 3. Ciberfisica

## Responsabilidade

Manter a representacao digital do ativo e os modelos que representam seu risco.
Na correspondencia da tese com o CRISP-DM, e nesta camada que ocorre a modelagem.

## Entradas

Features versionadas, configuracao do experimento e estado do ativo fisico.

## Saidas

- modelos candidatos e modelo aprovado;
- previsao de risco vinculada a uma versao;
- estado digital do equipamento;
- registro e artefatos de modelo.

## Componentes

- `algorithms/`: implementacoes e hiperparametros dos candidatos;
- `training.py`: treino reproduzivel e tracking;
- `inference.py`: carregamento do modelo em producao;
- `registry.py`: versoes, estagios, aprovacao e rollback;
- `assets.py`: estado digital da bomba ou motor.

## Evidencias de MLOps

Run, parametros, artefato, hash, versao, estagio, dataset, feature set e commit.
