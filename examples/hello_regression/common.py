import hashlib
import random
from typing import Dict, List


FEATURE_NAMES = ["intercept", "age", "sex", "exposure"]
TRUE_BETA = [1.5, 0.04, -0.6, 1.2]


SITE_CONFIGS = {
    "site-a": {"seed": 101, "n": 24, "age_mean": 45.0, "sex_prob": 0.40, "exposure_mean": -0.2},
    "site-b": {"seed": 202, "n": 32, "age_mean": 58.0, "sex_prob": 0.55, "exposure_mean": 0.5},
    "p33": {"seed": 303, "n": 28, "age_mean": 49.0, "sex_prob": 0.46, "exposure_mean": -0.1},
    "p697": {"seed": 404, "n": 30, "age_mean": 61.0, "sex_prob": 0.52, "exposure_mean": 0.35},
    "ukb-rap": {"seed": 505, "n": 34, "age_mean": 56.0, "sex_prob": 0.43, "exposure_mean": 0.8},
}


def _fallback_site_config(site_name: str) -> Dict[str, float]:
    digest = hashlib.sha256(site_name.encode("utf-8")).hexdigest()
    seed = int(digest[:8], 16)
    return {
        "seed": seed,
        "n": 20 + (seed % 12),
        "age_mean": 40.0 + (seed % 20),
        "sex_prob": 0.30 + ((seed % 40) / 100.0),
        "exposure_mean": ((seed % 7) - 3) / 4.0,
    }


def get_site_config(site_name: str) -> Dict[str, float]:
    cfg = SITE_CONFIGS.get(site_name, _fallback_site_config(site_name)).copy()
    cfg.setdefault("age_sd", 9.0)
    cfg.setdefault("exposure_sd", 1.0)
    cfg.setdefault("noise_sd", 0.8)
    return cfg


def compute_local_statistics(site_name: str) -> Dict[str, object]:
    cfg = get_site_config(site_name)
    rng = random.Random(cfg["seed"])

    n = int(cfg["n"])
    p = len(FEATURE_NAMES)
    x_tx = [[0.0 for _ in range(p)] for _ in range(p)]
    x_ty = [0.0 for _ in range(p)]
    y_ty = 0.0

    for _ in range(n):
        age = rng.gauss(cfg["age_mean"], cfg["age_sd"])
        sex = 1.0 if rng.random() < cfg["sex_prob"] else 0.0
        exposure = rng.gauss(cfg["exposure_mean"] + 0.3 * sex, cfg["exposure_sd"])
        noise = rng.gauss(0.0, cfg["noise_sd"])

        x = [1.0, age, sex, exposure]
        y = sum(beta * value for beta, value in zip(TRUE_BETA, x)) + noise

        for row in range(p):
            x_ty[row] += x[row] * y
            for col in range(p):
                x_tx[row][col] += x[row] * x[col]
        y_ty += y * y

    return {
        "site_name": site_name,
        "n": n,
        "p": p,
        "x_tx": x_tx,
        "x_ty": x_ty,
        "y_ty": float(y_ty),
        "feature_names": FEATURE_NAMES,
        "true_beta": TRUE_BETA,
        "site_config": cfg,
    }


def aggregate_statistics(local_stats: List[Dict[str, object]]) -> Dict[str, object]:
    import numpy as np

    if not local_stats:
        raise ValueError("no local statistics received")

    x_tx = np.zeros((len(FEATURE_NAMES), len(FEATURE_NAMES)), dtype=float)
    x_ty = np.zeros(len(FEATURE_NAMES), dtype=float)
    y_ty = 0.0
    total_n = 0

    for stats in local_stats:
        x_tx += np.asarray(stats["x_tx"], dtype=float)
        x_ty += np.asarray(stats["x_ty"], dtype=float)
        y_ty += float(stats["y_ty"])
        total_n += int(stats["n"])

    return {
        "x_tx": x_tx,
        "x_ty": x_ty,
        "y_ty": y_ty,
        "n": total_n,
        "p": len(FEATURE_NAMES),
    }


def solve_global_regression(aggregate: Dict[str, object]) -> Dict[str, object]:
    import numpy as np

    x_tx = np.asarray(aggregate["x_tx"], dtype=float)
    x_ty = np.asarray(aggregate["x_ty"], dtype=float)
    y_ty = float(aggregate["y_ty"])
    n = int(aggregate["n"])
    p = int(aggregate["p"])

    try:
        beta = np.linalg.solve(x_tx, x_ty)
        x_tx_inv = np.linalg.inv(x_tx)
    except np.linalg.LinAlgError:
        x_tx_inv = np.linalg.pinv(x_tx)
        beta = x_tx_inv @ x_ty

    residual_ss = max(y_ty - float(beta.T @ x_ty), 0.0)
    dof = max(n - p, 1)
    sigma2 = residual_ss / dof
    standard_error = np.sqrt(np.diag(x_tx_inv) * sigma2)

    return {
        "beta": beta,
        "standard_error": standard_error,
        "sigma2": float(sigma2),
        "residual_ss": float(residual_ss),
        "n": n,
        "p": p,
    }


def make_result_summary(local_stats: List[Dict[str, object]]) -> Dict[str, object]:
    aggregate = aggregate_statistics(local_stats)
    fit = solve_global_regression(aggregate)
    return {
        "feature_names": FEATURE_NAMES,
        "site_names": [stats["site_name"] for stats in local_stats],
        "total_samples": fit["n"],
        "per_site_samples": {stats["site_name"]: int(stats["n"]) for stats in local_stats},
        "true_beta": TRUE_BETA,
        "estimated_beta": fit["beta"].tolist(),
        "standard_error": fit["standard_error"].tolist(),
        "sigma2": fit["sigma2"],
        "residual_ss": fit["residual_ss"],
    }
