"""Fixed local RAW/HIDDEN features and sum-SSE unit-ridge gate regression."""
from collections.abc import Mapping

import numpy as np


def capped_count(answer_or_features):
    features = (answer_or_features["features"] if isinstance(answer_or_features, Mapping)
                else answer_or_features)
    features = np.asarray(features)
    if features.shape != (114,) or not np.isfinite(features).all():
        raise ValueError("finite original114 features required")
    return min(int(np.count_nonzero(features[3:63].reshape(20, 3)[:, 2] > 0)), 10)


def gate_features(answer, kind):
    if kind not in ("RAW", "HIDDEN"):
        raise ValueError("gate kind must be RAW or HIDDEN")
    features = np.asarray(answer["features"])
    if features.dtype != np.float32:
        raise ValueError("original114 FP32 features required")
    count = capped_count(features)
    onehot = np.zeros(11, dtype=np.float64)
    onehot[count] = 1.
    raw = np.concatenate((features.astype(np.float64), onehot))
    if kind == "RAW":
        return raw
    hidden = np.asarray(answer["hidden"])
    if hidden.shape != (128,) or hidden.dtype != np.float32 or not np.isfinite(hidden).all():
        raise ValueError("finite paid original128 FP32 hidden features required")
    return np.concatenate((raw, hidden.astype(np.float64)))


def _training(features, targets):
    if np.iscomplexobj(features) or np.iscomplexobj(targets):
        raise ValueError("real finite training arrays required")
    x, y = np.asarray(features, dtype=np.float64), np.asarray(targets, dtype=np.float64)
    if (x.ndim != 2 or not x.shape[0] or not x.shape[1] or y.shape != (len(x),)
            or not np.isfinite(x).all() or not np.isfinite(y).all()):
        raise ValueError("finite nonempty matrix and matching target vector required")
    return x, y


def _parameters(params, width):
    expected = {"mean", "scale", "constant", "coefficients", "intercept"}
    if set(params) != expected:
        raise ValueError("ridge artifact keys differ from the fixed contract")
    for key in ("mean", "scale", "coefficients"):
        value = np.asarray(params[key])
        if value.shape != (width,) or value.dtype != np.float64 or not np.isfinite(value).all():
            raise ValueError("invalid FP64 ridge parameter: " + key)
    constant = np.asarray(params["constant"])
    intercept = np.asarray(params["intercept"])
    if (constant.shape != (width,) or constant.dtype != np.bool_ or intercept.shape != ()
            or intercept.dtype != np.float64 or not np.isfinite(intercept)
            or np.any(params["scale"] <= 0) or np.any(params["scale"][constant] != 1.)):
        raise ValueError("invalid ridge scaler/intercept")


def predict(params, features):
    if np.iscomplexobj(features):
        raise ValueError("real features required")
    x = np.asarray(features, dtype=np.float64)
    if x.ndim not in (1, 2) or not x.shape[-1] or not np.isfinite(x).all():
        raise ValueError("finite feature row/matrix required")
    _parameters(params, x.shape[-1])
    value = ((x - params["mean"]) / params["scale"]) @ params["coefficients"] + params["intercept"]
    if not np.isfinite(value).all():
        raise FloatingPointError("nonfinite ridge prediction")
    return value


def fit_ridge(features, targets, *, name):
    x, y = _training(features, targets)
    constant = np.all(x == x[0], axis=0)
    mean = x.mean(axis=0, dtype=np.float64)
    mean[constant] = x[0, constant]
    scale = x.std(axis=0, ddof=0, dtype=np.float64)
    scale[constant] = 1.
    z = (x - mean) / scale
    zmean, ymean = z.mean(axis=0), y.mean(dtype=np.float64)
    centered = z - zmean
    gram = centered.T @ centered + np.eye(x.shape[1], dtype=np.float64)
    coefficients = np.linalg.solve(gram, centered.T @ (y - ymean))
    params = dict(mean=mean, scale=scale, constant=constant, coefficients=coefficients,
                  intercept=np.asarray(ymean - zmean @ coefficients, dtype=np.float64))
    diagnostics = audit_ridge(x, y, params)
    diagnostics.update(name=name, fits=1, optimizer_steps=0)
    return params, diagnostics


def audit_ridge(features, targets, params):
    """Recompute scaler, predictions, objective and stationarity; never refit.

    The relative infinity-norm residual is scaled by the normal equation's
    matrix/solution and RHS magnitudes. The bound allows FP64 reductions and
    dense linear algebra over n rows and p columns, without changing lambda.
    Conditioning is reported; it never triggers added regularization.
    """
    x, y = _training(features, targets)
    n, p = x.shape
    _parameters(params, p)
    constant = np.array([np.all(column == column[0]) for column in x.T])
    mean = np.sum(x, axis=0, dtype=np.float64) / n
    mean[constant] = x[0, constant]
    scale = np.sqrt(np.sum((x - mean) ** 2, axis=0, dtype=np.float64) / n)
    scale[constant] = 1.
    if (not np.array_equal(params["constant"], constant)
            or not np.array_equal(params["mean"], mean)
            or not np.array_equal(params["scale"], scale)):
        raise ValueError("ridge scaler differs from training-only population scaler")
    z = (x - mean) / scale
    design = np.column_stack((z, np.ones(n, dtype=np.float64)))
    penalty = np.diag(np.r_[np.ones(p), 0.])
    normal = design.T @ design + penalty
    rhs = design.T @ y
    solution = np.r_[params["coefficients"], params["intercept"]]
    predictions = design @ solution
    errors = predictions - y
    residual = normal @ solution - rhs
    magnitude = np.linalg.norm(normal, ord=np.inf) * np.linalg.norm(solution, ord=np.inf) + np.linalg.norm(rhs, ord=np.inf)
    relative = float(np.linalg.norm(residual, ord=np.inf) / max(float(magnitude), np.finfo(np.float64).tiny))
    tolerance = float(128 * np.finfo(np.float64).eps * max(n, p + 1))
    sse = float(errors @ errors)
    coefficient_penalty = float(params["coefficients"] @ params["coefficients"])
    condition = float(np.linalg.cond(normal))
    if (not np.isfinite(predictions).all() or not np.isfinite([sse, coefficient_penalty, relative, condition]).all()
            or relative > tolerance):
        raise FloatingPointError("ridge finite/stationarity audit failed")
    return dict(rows=n, columns=p, finite=True, scaler_matches=True, predictions=predictions.tolist(),
                sse=sse, coefficient_penalty=coefficient_penalty, objective=sse + coefficient_penalty,
                normal_condition_number=condition, normal_equation_residual_inf=float(np.linalg.norm(residual, ord=np.inf)),
                normal_equation_relative_residual=relative, residual_tolerance=tolerance, refits=0)
