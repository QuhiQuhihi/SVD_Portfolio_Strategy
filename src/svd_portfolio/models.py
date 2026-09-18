"""Centered PCA risk models and constrained minimum-variance allocation."""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf


@dataclass
class PCAFit:
    covariance: np.ndarray
    explained_variance_ratio: np.ndarray
    loadings: np.ndarray
    eigenvalues: np.ndarray


def _matrix(returns) -> np.ndarray:
    x = np.asarray(returns, dtype=float)
    if x.ndim != 2 or x.shape[0] < 3 or x.shape[1] < 2 or not np.isfinite(x).all():
        raise ValueError("Need a finite T by N return matrix with T >= 3 and N >= 2")
    if np.any(x.std(axis=0, ddof=1) < 1e-12):
        raise ValueError("A training asset has effectively zero variance")
    return x


def pca_covariance(returns, n_components: int, space: str = "covariance") -> PCAFit:
    """Rank-k common covariance plus diagonal residual risk (daily units).

    SVD is applied to centered returns, or centered training-standardized returns.
    Unlike a rank-k truncation alone, diagonal residual risk is retained. Taking the
    absolute value of eigenvectors is never part of covariance estimation.
    """
    x = _matrix(returns)
    if not 1 <= n_components <= min(x.shape):
        raise ValueError("Invalid PCA rank")
    if space not in ("covariance", "correlation"):
        raise ValueError("Unknown PCA space")
    centered = x - x.mean(axis=0)
    scale = x.std(axis=0, ddof=1) if space == "correlation" else np.ones(x.shape[1])
    standardized = centered / scale
    _, singular_values, vt = np.linalg.svd(standardized, full_matrices=False)
    eigenvalues = singular_values**2 / (len(x) - 1)
    loadings = vt.T
    common = (loadings[:, :n_components] * eigenvalues[:n_components]) @ (
        loadings[:, :n_components].T
    )
    total_variance = standardized.var(axis=0, ddof=1)
    residual_variance = np.maximum(total_variance - np.diag(common), 0)
    covariance = (common + np.diag(residual_variance)) * np.outer(scale, scale)
    return PCAFit(covariance, eigenvalues / eigenvalues.sum(), loadings, eigenvalues)


def covariance_models(returns, n_components: int, space: str) -> tuple[dict, PCAFit]:
    x = _matrix(returns)
    pca = pca_covariance(x, n_components, space)
    # sklearn uses 1/T. Express all estimators in 1/(T-1) sample-variance units.
    shrinkage = LedoitWolf().fit(x).covariance_ * len(x) / (len(x) - 1)
    return {
        "Sample": np.cov(x, rowvar=False, ddof=1),
        "Ledoit-Wolf": shrinkage,
        "PCA": pca.covariance,
    }, pca


def capped_proportional(scores, cap: float) -> np.ndarray:
    """Proportionally allocate positive scores subject to a per-asset cap."""
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not np.isfinite(scores).all() or (scores <= 0).any():
        raise ValueError("Scores must be finite and positive")
    if not 0 < cap <= 1 or len(scores) * cap < 1 - 1e-12:
        raise ValueError("Infeasible weight cap")
    weights, active = np.zeros(len(scores)), np.ones(len(scores), dtype=bool)
    while active.any():
        proposal = (1 - weights.sum()) * scores[active] / scores[active].sum()
        binding = proposal > cap + 1e-12
        indices = np.flatnonzero(active)
        if not binding.any():
            weights[indices] = proposal
            break
        weights[indices[binding]] = cap
        active[indices[binding]] = False
    return weights


def minimum_variance(covariance, cap: float) -> np.ndarray:
    covariance = np.asarray(covariance, dtype=float)
    n = len(covariance)
    if covariance.shape != (n, n) or not np.isfinite(covariance).all():
        raise ValueError("Invalid covariance matrix")
    if not np.allclose(covariance, covariance.T, rtol=1e-9, atol=1e-12):
        raise ValueError("Covariance must be symmetric")
    if not 0 < cap <= 1 or n * cap < 1 - 1e-12:
        raise ValueError("Infeasible weight cap")
    if np.linalg.eigvalsh(covariance).min() < -1e-10:
        raise ValueError("Covariance must be positive semidefinite")
    if np.trace(covariance) <= 0:
        raise ValueError("Covariance has no risk")
    # Normalize objective to prevent premature SLSQP convergence on daily variances.
    scaled = covariance / (np.trace(covariance) / n)
    result = minimize(
        lambda w: w @ scaled @ w,
        np.full(n, 1 / n),
        jac=lambda w: 2 * scaled @ w,
        method="SLSQP",
        bounds=[(0.0, cap)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1, "jac": lambda w: np.ones(n)}],
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(f"Portfolio optimization failed: {result.message}")
    weights = result.x
    if abs(weights.sum() - 1) > 1e-8 or weights.min() < -1e-8 or weights.max() > cap + 1e-8:
        raise RuntimeError("Optimizer returned infeasible weights")
    return weights
