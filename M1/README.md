# Módulo 1 - Fundamentos de Dados e Aprendizado de Máquina

Este módulo reúne as práticas do OpAIoT voltadas aos fundamentos de análise de dados e aprendizado de máquina aplicados a problemas industriais. As atividades são notebooks do Google Colab que evoluem da estatística descritiva até a modelagem preditiva com scikit-learn, sempre sobre bases sintéticas de sensores industriais (temperatura, pressão, vibração, etc.) geradas no próprio notebook.

Este repositório publica notebooks para as Aulas 1 a 26, exceto a Aula 6: ela é teórica, sem prática de código associada, por isso não aparece aqui.

## Ordem sugerida

1. Comece pelas [Aulas 1-5 - Estatística Descritiva](colab/M1_Aulas_1_5_Aplicação_Prática_01.ipynb) para praticar medidas de localização/espalhamento, distribuições e correlação com Pandas.
2. Siga para as [Aulas 7-9 - Tratamento de Dados](colab/M1_Aulas_7_9_Aplicação_Prática_02.ipynb) e trate valores ausentes, duplicatas, inconsistências e outliers.
3. Avance para as [Aulas 10-15 - Transformação e Seleção de Atributos](colab/M1_Aulas_10_15_Aplicação_Prática_03.ipynb) com encoding, discretização, escalonamento e seleção de variáveis.
4. Feche o módulo com as [Aulas 16-26 - Modelagem Preditiva](colab/M1_Aulas_16_26_Aplicação_Prática_04.ipynb), que cobre regressão, classificação e `Pipeline` do scikit-learn.

## Aulas

| Aulas | Notebook | Conteúdo |
| --- | --- | --- |
| 1-5 | [M1_Aulas_1_5_Aplicação_Prática_01.ipynb](colab/M1_Aulas_1_5_Aplicação_Prática_01.ipynb) | Estatística descritiva e visualização multivariada: medidas de localização e espalhamento, quantis, boxplot, obliquidade/curtose, matriz de correlação (heatmap), scatter plots e agregações com `groupby`. |
| 7-9 | [M1_Aulas_7_9_Aplicação_Prática_02.ipynb](colab/M1_Aulas_7_9_Aplicação_Prática_02.ipynb) | Tratamento de dados: diagnóstico de valores ausentes, remoção de duplicatas e atributos redundantes, padronização de categorias e datas, imputação (média/mediana/moda) e detecção de outliers (IQR, z-score, DBSCAN). |
| 10-15 | [M1_Aulas_10_15_Aplicação_Prática_03.ipynb](colab/M1_Aulas_10_15_Aplicação_Prática_03.ipynb) | Transformação de dados e seleção de atributos: encoding de categorias (One-Hot, Ordinal, Frequency), discretização (largura/frequência igual, k-means), escalonamento (Standard/MinMax/Robust) e seleção de atributos (Filter, Wrapper/RFE, Embedded/Lasso, importância em árvores). |
| 16-26 | [M1_Aulas_16_26_Aplicação_Prática_04.ipynb](colab/M1_Aulas_16_26_Aplicação_Prática_04.ipynb) | Modelagem preditiva com scikit-learn: regressão (Linear, Ridge, Lasso) e classificação (Logística, Árvore de Decisão, Random Forest, XGBoost), métricas (MAE/RMSE/R², matriz de confusão, ROC/AUC) e `Pipeline` com busca de hiperparâmetros. |

## Estrutura

```text
M1/
└── colab/
    ├── M1_Aulas_1_5_Aplicação_Prática_01.ipynb
    ├── M1_Aulas_7_9_Aplicação_Prática_02.ipynb
    ├── M1_Aulas_10_15_Aplicação_Prática_03.ipynb
    └── M1_Aulas_16_26_Aplicação_Prática_04.ipynb
```

## Ambiente de execução

### Google Colab

Caminho recomendado. A primeira célula de cada notebook traz o selo "Open in Colab": clique nele para abrir e executar direto no navegador, sem instalar nada. As bases de dados são sintéticas e geradas pelo próprio notebook, sem necessidade de upload de arquivo.

### Jupyter local

Os notebooks também rodam em Jupyter/JupyterLab local ou no VS Code, desde que as bibliotecas usadas estejam instaladas: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy` e `scikit-learn` em todos eles, e `xgboost` a partir das Aulas 16-26.

## Requisitos gerais

- Conta Google, para abrir e executar os notebooks no Colab (recomendado).
- Alternativamente, Python 3 com Jupyter e as bibliotecas listadas acima.
- Git para clonar o repositório.

Cada notebook comenta, em células de "Interpretação" ao longo do texto, o racional de cada etapa. Use este README como índice do módulo e siga a ordem sugerida antes de pular para tópicos avançados.

[Voltar ao início do curso](../README.md)
