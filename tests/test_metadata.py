"""Tests for metadata module."""

import pytest

from docsplit.metadata import calculate_confidence
from docsplit.models import DocumentMetadata, DocumentType


def test_confidence_full_metadata():
    """Test confidence scoring with complete metadata."""
    meta = DocumentMetadata(
        vendor="Huntington Bank",
        date="2025-01-15",
        document_type=DocumentType.STATEMENT,
    )

    score = calculate_confidence(meta, "")

    # Full vendor (0.4 + 0.1) + full date (0.3 + 0.1) + type (0.2) = 1.1 -> 1.0
    assert score == 1.0


def test_confidence_partial_metadata():
    """Test confidence scoring with partial metadata."""
    meta = DocumentMetadata(
        vendor="Test",  # Too short for bonus
        date="2025-01",  # Month only
        document_type=DocumentType.STATEMENT,
    )

    score = calculate_confidence(meta, "")

    # Vendor 0.4 (no bonus) + date 0.3 (no bonus) + type 0.2 = 0.9
    assert score == pytest.approx(0.9)


def test_confidence_missing_vendor():
    """Test confidence scoring with missing vendor."""
    meta = DocumentMetadata(
        vendor="Unknown", date="2025-01-15", document_type=DocumentType.INVOICE
    )

    score = calculate_confidence(meta, "")

    # No vendor (0.0) + full date (0.4) + type (0.2) = 0.6
    assert score == pytest.approx(0.6)


def test_confidence_minimal_metadata():
    """Test confidence scoring with minimal metadata."""
    meta = DocumentMetadata()  # All defaults

    score = calculate_confidence(meta, "")

    # Unknown vendor, no date, OTHER type = 0.0
    assert score == 0.0
