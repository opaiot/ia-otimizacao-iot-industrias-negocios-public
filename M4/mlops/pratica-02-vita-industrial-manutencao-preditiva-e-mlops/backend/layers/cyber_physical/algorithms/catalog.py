"""Catalogo didatico dos algoritmos usados no experimento."""

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression


def candidate_algorithms(seed: int) -> dict:
    """Retorna candidatos com configuracoes explicitas e reproduziveis."""
    return {
        "LogisticRegression": LogisticRegression(
            max_iter=400,
            class_weight="balanced",
            solver="liblinear",
            random_state=seed,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            class_weight="balanced",
            random_state=seed,
        ),
        "GradientBoosting": GradientBoostingClassifier(random_state=seed),
    }
