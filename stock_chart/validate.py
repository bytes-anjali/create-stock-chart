"""Validate that a stylized (smoothed) series preserves the raw series' pattern.

This is the "compare the generated chart against the Yahoo data/path" step: it
checks that stylizing the line hasn't added, dropped, reordered, or shifted a
material peak/trough, and hasn't reversed the overall direction of movement.
"""

from dataclasses import dataclass, field

from .pattern import find_extrema


@dataclass
class ValidationResult:
    ok: bool
    reasons: list = field(default_factory=list)


def validate_pattern(
    raw_prices,
    styled_prices,
    index_tolerance_frac: float = 0.03,
    value_tolerance_frac: float = 0.01,
) -> ValidationResult:
    raw_extrema = find_extrema(raw_prices)
    styled_extrema = find_extrema(styled_prices)

    reasons = []
    n = len(raw_prices)
    idx_tol = max(1, int(n * index_tolerance_frac))

    if len(raw_extrema) != len(styled_extrema):
        reasons.append(
            f"extrema count mismatch: raw={len(raw_extrema)} styled={len(styled_extrema)}"
        )
        return ValidationResult(False, reasons)

    for (raw_i, raw_kind), (styled_i, styled_kind) in zip(raw_extrema, styled_extrema):
        if raw_kind != styled_kind:
            reasons.append(f"extrema kind mismatch at raw idx {raw_i}: {raw_kind} vs {styled_kind}")
            continue
        if abs(raw_i - styled_i) > idx_tol:
            reasons.append(f"{raw_kind} at {raw_i} shifted to {styled_i} (tolerance {idx_tol})")

        raw_value = raw_prices[raw_i]
        styled_value = styled_prices[styled_i]
        if raw_value and abs(raw_value - styled_value) / abs(raw_value) > value_tolerance_frac:
            reasons.append(f"{raw_kind} value drift at {raw_i}: raw={raw_value:.4f} styled={styled_value:.4f}")

    raw_direction = raw_prices[-1] - raw_prices[0]
    styled_direction = styled_prices[-1] - styled_prices[0]
    if raw_direction * styled_direction < 0:
        reasons.append("overall direction reversed")

    return ValidationResult(len(reasons) == 0, reasons)
