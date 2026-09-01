"""Direct computation receipt for the immutable raw-value control."""

from fractions import Fraction

from ..controls.raw_value import RAW_VALUE_ROWS, balanced_accuracy


def raw_control_receipt() -> dict:
    classifier = lambda raw_values: int(raw_values[0] > 0)  # deterministic raw-only fixture rule
    accuracy = balanced_accuracy(classifier)
    if accuracy != Fraction(1, 2):
        raise RuntimeError("B01 raw-value control fixture no longer equals exactly one half")
    return {
        "schema": "FRRIE_B01_RAW_CONTROL_RECEIPT_V1",
        "rows": [
            {
                "pair_id": row.pair_id,
                "raw_values": [str(value) for value in row.raw_values],
                "label": row.label, "association": row.association,
                "prediction": classifier(row.raw_values),
            }
            for row in RAW_VALUE_ROWS
        ],
        "balanced_accuracy_numerator": accuracy.numerator,
        "balanced_accuracy_denominator": accuracy.denominator,
        "balanced_accuracy": float(accuracy),
        "conformance_passed": True,
        "output_disconnected": True,
        "complete": True,
    }
