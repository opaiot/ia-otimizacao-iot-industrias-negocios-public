# Incidente, retirada e rollback

1. Registrar o alerta, impacto, versao e responsavel na trilha de auditoria.
2. Confirmar se a causa esta em dados, features, modelo, integracao ou operacao.
3. Suspender a recomendacao automatizada quando o risco nao estiver controlado.
4. Restaurar apenas uma versao anterior aprovada e com artefato verificavel.
5. Validar o servico restaurado e comunicar as partes afetadas.
6. Atualizar model card, datasheet, monitoramento e relatorio de rastreabilidade.
7. Abrir um novo experimento quando a correcao exigir dados ou modelo diferentes.

O rollback nao apaga o incidente nem sobrescreve evidencias historicas.
