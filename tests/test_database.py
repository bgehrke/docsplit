"""Tests for database module."""

import tempfile
from pathlib import Path

import pytest

from docsplit.database import Database
from docsplit.models import Batch, Document, DocumentMetadata, DocumentType, ProcessingStatus


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = Database(db_path)
    yield db

    # Cleanup
    db_path.unlink()


def test_create_batch(temp_db):
    """Test creating a batch record."""
    batch = Batch(source_path=Path("/tmp/test.pdf"))
    batch_id = temp_db.create_batch(batch)

    assert batch_id > 0

    # Verify
    summary = temp_db.get_batch_summary(batch_id)
    assert summary is not None
    assert summary["source_path"] == str(batch.source_path)


def test_create_document(temp_db):
    """Test creating a document record."""
    # Create batch first
    batch = Batch(source_path=Path("/tmp/test.pdf"))
    batch_id = temp_db.create_batch(batch)

    # Create document
    meta = DocumentMetadata(vendor="TestCo", date="2025-01", document_type=DocumentType.INVOICE)

    doc = Document(
        batch_id=batch_id,
        source_path=Path("/tmp/doc.pdf"),
        archive_path=Path("/archive/2025/01/2025-01_TestCo_Inv.pdf"),
        metadata=meta,
        status=ProcessingStatus.SUCCESS,
        confidence_score=0.85,
    )

    doc_id = temp_db.create_document(doc)
    assert doc_id > 0


def test_search_documents(temp_db):
    """Test document search."""
    # Create batch
    batch = Batch(source_path=Path("/tmp/test.pdf"))
    batch_id = temp_db.create_batch(batch)

    # Create multiple documents
    docs = [
        Document(
            batch_id=batch_id,
            source_path=Path("/tmp/doc1.pdf"),
            metadata=DocumentMetadata(
                vendor="Huntington Bank", date="2025-01", document_type=DocumentType.STATEMENT
            ),
            status=ProcessingStatus.SUCCESS,
        ),
        Document(
            batch_id=batch_id,
            source_path=Path("/tmp/doc2.pdf"),
            metadata=DocumentMetadata(
                vendor="ComEd", date="2025-02", document_type=DocumentType.BILL
            ),
            status=ProcessingStatus.SUCCESS,
        ),
        Document(
            batch_id=batch_id,
            source_path=Path("/tmp/doc3.pdf"),
            metadata=DocumentMetadata(
                vendor="Verizon", date="2025-01", document_type=DocumentType.BILL
            ),
            status=ProcessingStatus.FAILED,
            error_message="Test error",
        ),
    ]

    for doc in docs:
        temp_db.create_document(doc)

    # Search by vendor
    results = temp_db.search_documents(vendor="Huntington")
    assert len(results) == 1
    assert results[0]["vendor"] == "Huntington Bank"

    # Search by year
    results = temp_db.search_documents(year=2025)
    assert len(results) == 3

    # Search by status
    results = temp_db.search_documents(status=ProcessingStatus.FAILED)
    assert len(results) == 1
    assert results[0]["vendor"] == "Verizon"


def test_update_batch_counts(temp_db):
    """Test updating batch statistics."""
    batch = Batch(source_path=Path("/tmp/test.pdf"))
    batch_id = temp_db.create_batch(batch)

    temp_db.update_batch_counts(batch_id, total=10, success=8, errors=2)

    summary = temp_db.get_batch_summary(batch_id)
    assert summary["total_docs"] == 10
    assert summary["success_count"] == 8
    assert summary["error_count"] == 2
