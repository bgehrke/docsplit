"""Tests for data models."""

from datetime import datetime

from docsplit.models import Document, DocumentMetadata, DocumentType, ProcessingStatus


def test_document_metadata_defaults():
    """Test DocumentMetadata with defaults."""
    meta = DocumentMetadata()
    assert meta.vendor == "Unknown"
    assert meta.date is None
    assert meta.document_type == DocumentType.OTHER


def test_document_metadata_validation():
    """Test DocumentMetadata date validation."""
    # Valid dates
    meta1 = DocumentMetadata(vendor="Test", date="2025-01")
    assert meta1.date == "2025-01"

    meta2 = DocumentMetadata(vendor="Test", date="2025-01-15")
    assert meta2.date == "2025-01-15"

    # Invalid date
    meta3 = DocumentMetadata(vendor="Test", date="invalid")
    assert meta3.date is None


def test_document_creation():
    """Test Document model."""
    from pathlib import Path

    meta = DocumentMetadata(vendor="TestCo", date="2025-01", document_type=DocumentType.INVOICE)

    doc = Document(
        source_path=Path("/tmp/test.pdf"),
        metadata=meta,
        status=ProcessingStatus.SUCCESS,
    )

    assert doc.metadata.vendor == "TestCo"
    assert doc.status == ProcessingStatus.SUCCESS
    assert isinstance(doc.created_at, datetime)
