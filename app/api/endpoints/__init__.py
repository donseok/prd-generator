"""API endpoints package."""

from . import health
from . import documents
from . import processing
from . import prd
from . import review

__all__ = ["health", "documents", "processing", "prd", "review"]
