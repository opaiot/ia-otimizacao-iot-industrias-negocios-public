# Protocolo de rastreamento e registro

## Antes do treino

- identificar e validar a versao dos dados;
- congelar seed, split, features, limiar e dependencias;
- registrar objetivo, risco operacional e criterios de avaliacao.

## Durante o treino

- atribuir identidade a cada run;
- salvar parametros, metricas, artefatos e responsavel;
- comparar custo do erro, robustez e governanca, nao apenas acuracia.

## Antes da promocao

- confirmar que o artefato pode ser carregado;
- vincular run, dados, features, codigo, metricas, model card e datasheet;
- exigir aprovacao humana e plano de rollback.

## Estados do modelo

O projeto usa `production` e `archived` de forma simplificada. Em uma implantacao
real, recomenda-se explicitar candidato, validado, aprovado, producao e retirado.
