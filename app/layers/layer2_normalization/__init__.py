"""Layer 2: Normalization - Convert parsed content to structured requirements."""

from .normalizer import Normalizer
from .confidence_calculator import (
    ConfidenceCalculator,
    ConfidenceBreakdown,
    get_confidence_calculator,
)

__all__ = [
    "Normalizer",
    "ConfidenceCalculator",
    "ConfidenceBreakdown",
    "get_confidence_calculator",
]
