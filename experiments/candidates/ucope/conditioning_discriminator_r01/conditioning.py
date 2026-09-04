"""Target-blind FP32 coordinate conditioning with fail-closed Cholesky."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import struct
from typing import Any

from .contract import ROOT_BASIS_DIM, TAIL_BASIS_DIM

TRANSFORM_SCHEMA = "UCOPE_BC_CONDITIONING_R01_TRANSFORM_V1"
STAGE_DIMS = {"tail": TAIL_BASIS_DIM, "root": ROOT_BASIS_DIM}
_FP32_EPS = 2.0 ** -23
_SCORE_RTOL = 32.0 * _FP32_EPS
_SCORE_ATOL = 32.0 * _FP32_EPS


class ConditioningTransformError(ValueError):
    """A feature-only conditioning transform cannot be formed or verified."""


def _torch():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("UCOPE conditioning requires PyTorch") from exc
    return torch


def _canonical_fp32_bytes(tensor: Any) -> bytes:
    """Return row-major little-endian FP32 bytes without a NumPy dependency."""
    torch = _torch()
    cpu = tensor.detach().to(device="cpu", dtype=torch.float32).contiguous()
    values = cpu.reshape(-1).tolist()
    return b"".join(struct.pack("<f", value) for value in values)


def _decode_fp32(data: bytes, rows: int, columns: int):
    torch = _torch()
    expected = rows * columns * 4
    if len(data) != expected:
        raise ConditioningTransformError("canonical matrix byte length mismatch")
    values = [value[0] for value in struct.iter_unpack("<f", data)]
    return torch.tensor(values, dtype=torch.float32).reshape(rows, columns)


def _design_digest(matrix: Any) -> str:
    header = struct.pack("<QQ", int(matrix.shape[0]), int(matrix.shape[1]))
    return hashlib.sha256(header + _canonical_fp32_bytes(matrix)).hexdigest()


def _require_feature_matrix(features: Any, *, expected_dim: int, label: str):
    torch = _torch()
    if not isinstance(features, torch.Tensor):
        raise ConditioningTransformError(f"{label} must be a torch.Tensor")
    if features.dtype != torch.float32 or features.ndim != 2:
        raise ConditioningTransformError(f"{label} must be an ordered rank-2 FP32 matrix")
    if features.shape[0] <= 0 or features.shape[1] != expected_dim:
        raise ConditioningTransformError(f"{label} feature dimension mismatch")
    if features.requires_grad:
        raise ConditioningTransformError(f"{label} must be detached feature data")
    if not torch.isfinite(features).all().item():
        raise ConditioningTransformError(f"{label} must contain only finite features")
    return features


@dataclass(frozen=True)
class TransformRecord:
    """Immutable feature-only bytes sufficient to bind a later coordinate map."""

    schema: str
    stage: str
    row_count: int
    feature_dim: int
    ordered_design_sha256: str
    gram_fp32_le: bytes
    cholesky_lower_fp32_le: bytes

    def validate(self) -> "TransformRecord":
        torch = _torch()
        if self.schema != TRANSFORM_SCHEMA or self.stage not in STAGE_DIMS:
            raise ConditioningTransformError("transform schema/stage drift")
        if type(self.row_count) is not int or self.row_count <= 0:
            raise ConditioningTransformError("transform row count must be positive")
        if self.feature_dim != STAGE_DIMS[self.stage]:
            raise ConditioningTransformError("transform stage/dimension mismatch")
        if (
            type(self.ordered_design_sha256) is not str
            or len(self.ordered_design_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.ordered_design_sha256)
        ):
            raise ConditioningTransformError("ordered design digest is not lowercase SHA-256")
        gram = self.gram_matrix()
        lower = self.lower_matrix()
        if not torch.isfinite(gram).all().item() or not torch.isfinite(lower).all().item():
            raise ConditioningTransformError("transform record contains nonfinite values")
        if not torch.equal(lower, torch.tril(lower)):
            raise ConditioningTransformError("recorded Cholesky factor is not lower triangular")
        diagonal = torch.diagonal(lower)
        if not torch.isfinite(diagonal).all().item() or not torch.all(diagonal > 0).item():
            raise ConditioningTransformError("Cholesky diagonal must be finite and positive")
        reconstructed = lower @ lower.transpose(0, 1)
        if not torch.allclose(reconstructed, gram, rtol=16 * _FP32_EPS, atol=16 * _FP32_EPS):
            raise ConditioningTransformError("recorded Gram/Cholesky relation is invalid")
        return self

    def gram_matrix(self):
        return _decode_fp32(self.gram_fp32_le, self.feature_dim, self.feature_dim)

    def lower_matrix(self):
        return _decode_fp32(self.cholesky_lower_fp32_le, self.feature_dim, self.feature_dim)

    def to_bytes(self) -> bytes:
        """Canonical deterministic state serialization (no target/outcome fields)."""
        self.validate()
        payload = {
            "cholesky_lower_fp32_le": self.cholesky_lower_fp32_le.hex(),
            "feature_dim": self.feature_dim,
            "gram_fp32_le": self.gram_fp32_le.hex(),
            "ordered_design_sha256": self.ordered_design_sha256,
            "row_count": self.row_count,
            "schema": self.schema,
            "stage": self.stage,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

    @classmethod
    def from_bytes(cls, data: bytes) -> "TransformRecord":
        try:
            payload = json.loads(data.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ConditioningTransformError("invalid transform record serialization") from exc
        required = {
            "cholesky_lower_fp32_le",
            "feature_dim",
            "gram_fp32_le",
            "ordered_design_sha256",
            "row_count",
            "schema",
            "stage",
        }
        if not isinstance(payload, dict) or set(payload) != required:
            raise ConditioningTransformError("transform record field inventory mismatch")
        try:
            record = cls(
                schema=payload["schema"],
                stage=payload["stage"],
                row_count=payload["row_count"],
                feature_dim=payload["feature_dim"],
                ordered_design_sha256=payload["ordered_design_sha256"],
                gram_fp32_le=bytes.fromhex(payload["gram_fp32_le"]),
                cholesky_lower_fp32_le=bytes.fromhex(payload["cholesky_lower_fp32_le"]),
            )
        except (TypeError, ValueError) as exc:
            raise ConditioningTransformError("invalid transform record field encoding") from exc
        return record.validate()


@dataclass(frozen=True)
class GramDesignRecord:
    stage: str
    row_count: int
    feature_dim: int
    ordered_design_sha256: str
    gram_fp32_le: bytes

    def gram_matrix(self):
        return _decode_fp32(self.gram_fp32_le, self.feature_dim, self.feature_dim)


def build_gram_design(stage: str, training_features: Any) -> GramDesignRecord:
    if stage not in STAGE_DIMS: raise ConditioningTransformError("stage must be tail or root")
    matrix = _require_feature_matrix(training_features, expected_dim=STAGE_DIMS[stage], label="training_features")
    gram = matrix.transpose(0, 1) @ matrix / matrix.shape[0]
    return GramDesignRecord(stage, int(matrix.shape[0]), int(matrix.shape[1]), _design_digest(matrix), _canonical_fp32_bytes(gram))


def factor_gram_design(design: GramDesignRecord) -> TransformRecord:
    torch = _torch(); gram = design.gram_matrix()
    try: lower = torch.linalg.cholesky(gram, upper=False)
    except RuntimeError as exc: raise ConditioningTransformError("training-feature Gram matrix is not positive definite") from exc
    diagonal = torch.diagonal(lower)
    if not torch.isfinite(lower).all().item() or not torch.all(diagonal > 0).item(): raise ConditioningTransformError("Cholesky factor lacks a finite positive diagonal")
    return TransformRecord(TRANSFORM_SCHEMA, design.stage, design.row_count, design.feature_dim, design.ordered_design_sha256, design.gram_fp32_le, _canonical_fp32_bytes(lower)).validate()


@dataclass(frozen=True)
class ScoreEquivalence:
    """Direct evidence that paired raw/whitened initialization scores agree."""

    raw_beta0: Any
    whitened_beta0: Any
    raw_scores: Any
    whitened_scores: Any
    exact: bool
    maximum_absolute_error: float


def build_transform(stage: str, training_features: Any) -> TransformRecord:
    """Build G=X.T@X/n and its lower Cholesky from training features only."""
    # There is intentionally no ridge, truncation, retry, or factor repair.
    return factor_gram_design(build_gram_design(stage, training_features))


def transform_features(record: TransformRecord, features: Any):
    """Apply z_w=L^-1 z using columns internally and return row features."""
    torch = _torch()
    record.validate()
    matrix = _require_feature_matrix(features, expected_dim=record.feature_dim, label="features")
    lower = record.lower_matrix().to(device=matrix.device)
    # Each external row is one feature vector z. solve_triangular expects the
    # column convention L z_w = z, so the batch is transposed in and back out.
    transformed_columns = torch.linalg.solve_triangular(lower, matrix.transpose(0, 1), upper=False)
    transformed = transformed_columns.transpose(0, 1).contiguous()
    if transformed.dtype != torch.float32 or not torch.isfinite(transformed).all().item():
        raise ConditioningTransformError("whitened features are not finite FP32")
    return transformed


def pair_initial_coefficients(
    record: TransformRecord,
    raw_beta0: Any,
    candidate_features: Any,
) -> ScoreEquivalence:
    """Set beta_tilde0=L.T@beta0 and verify paired candidate scores."""
    torch = _torch()
    record.validate()
    if not isinstance(raw_beta0, torch.Tensor):
        raise ConditioningTransformError("raw_beta0 must be a torch.Tensor")
    if raw_beta0.dtype != torch.float32 or raw_beta0.ndim != 1 or raw_beta0.shape[0] != record.feature_dim:
        raise ConditioningTransformError("raw_beta0 must be a stage-sized FP32 vector")
    if raw_beta0.requires_grad or not torch.isfinite(raw_beta0).all().item():
        raise ConditioningTransformError("raw_beta0 must be detached and finite")
    candidates = _require_feature_matrix(
        candidate_features,
        expected_dim=record.feature_dim,
        label="candidate_features",
    )
    lower = record.lower_matrix().to(device=raw_beta0.device)
    if candidates.device != raw_beta0.device:
        raise ConditioningTransformError("candidate features and beta0 must share a device")
    whitened_beta0 = lower.transpose(0, 1) @ raw_beta0
    whitened_candidates = transform_features(record, candidates)
    raw_scores = candidates @ raw_beta0
    whitened_scores = whitened_candidates @ whitened_beta0
    if not torch.isfinite(whitened_beta0).all().item() or not torch.isfinite(whitened_scores).all().item():
        raise ConditioningTransformError("paired initialization produced nonfinite values")
    exact = torch.equal(raw_scores, whitened_scores)
    if not torch.allclose(raw_scores, whitened_scores, rtol=_SCORE_RTOL, atol=_SCORE_ATOL):
        error = float(torch.max(torch.abs(raw_scores - whitened_scores)).item())
        raise ConditioningTransformError(f"paired initial candidate scores differ in FP32: max_abs={error}")
    maximum_error = float(torch.max(torch.abs(raw_scores - whitened_scores)).item()) if raw_scores.numel() else 0.0
    return ScoreEquivalence(
        raw_beta0=raw_beta0.detach().clone(),
        whitened_beta0=whitened_beta0.detach().clone(),
        raw_scores=raw_scores.detach().clone(),
        whitened_scores=whitened_scores.detach().clone(),
        exact=bool(exact),
        maximum_absolute_error=maximum_error,
    )
