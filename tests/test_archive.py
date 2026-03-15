"""Tests for archive module."""

from pathlib import Path

import pytest

from docsplit.archive import (
    generate_filename,
    sanitize_filename,
    strip_filler_words,
)
from docsplit.models import DocumentMetadata, DocumentType


def test_strip_filler_words():
    """Test filler word removal."""
    assert strip_filler_words("The Huntington National Bank") == "Huntington National Bank"
    assert strip_filler_words("Farmer, Poklop, Hoppa & Co.") == "Farmer, Poklop, Hoppa"
    assert strip_filler_words("Test LLC") == "Test"
    assert strip_filler_words("Company Name Inc") == "Name"


def test_sanitize_filename():
    """Test filename sanitization."""
    assert sanitize_filename("Test Company") == "Test_Company"
    assert sanitize_filename("Test/Company\\Name") == "Test_Company_Name"
    assert sanitize_filename("Test___Company") == "Test_Company"
    assert sanitize_filename("_Test_") == "Test"


def test_generate_filename():
    """Test filename generation."""
    meta = DocumentMetadata(
        vendor="The Huntington Bank LLC",
        date="2025-01-15",
        document_type=DocumentType.STATEMENT,
    )

    filename = generate_filename(meta)
    assert filename == "2025-01_Huntington_Bank_Stmt.pdf"


def test_generate_filename_with_invalid_date():
    """Test filename generation with invalid date."""
    meta = DocumentMetadata(
        vendor="Test Vendor",
        date=None,
        document_type=DocumentType.INVOICE,
    )

    filename = generate_filename(meta)
    # Should use current year-month
    assert filename.endswith("_Test_Vendor_Inv.pdf")
    assert len(filename.split("_")[0]) == 7  # YYYY-MM
