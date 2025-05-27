"""Helper functions for quantiative evaluation of solutions."""

import tiktoken


def is_exact_match(pred: int | str | list, target: int | str | list) -> bool:
    """Return True if the prediction is an exact match to the target."""
    return pred == target


def is_exact_match_lower(pred: str, target: str) -> bool:
    """Return True if the prediction is an exact match to the target."""
    return pred.strip().lower() == target.strip().lower()


def is_in_range(pred: int | float, target: int | float, tolerance: float) -> bool:
    """Return True if the prediction is within the target range."""
    return target - tolerance <= pred <= target + tolerance


def is_subset(pred: list, target: list) -> bool:
    """Return True if the prediction is a subset of the target."""
    return set(pred).issubset(set(target))


def is_superset(pred: list, target: list) -> bool:
    """Return True if the prediction is a superset of the target."""
    return set(pred).issuperset(set(target))
