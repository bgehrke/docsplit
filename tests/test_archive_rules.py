"""Tests for archive routing rules."""

from pathlib import Path

import pytest

from docsplit.archive import get_archive_path, match_archive_rules
from docsplit.config import ArchiveRule
from docsplit.models import DocumentMetadata, DocumentType


def test_manual_override():
    """Test manual destination override."""
    meta = DocumentMetadata(vendor="TestCo", date="2025-01", document_type=DocumentType.INVOICE)

    archive_root = Path("/archive")
    path = get_archive_path(archive_root, meta, override="2025/tax-documents")

    assert path == Path("/archive/2025/tax-documents")


def test_manual_override_with_template():
    """Test manual override with template variables."""
    meta = DocumentMetadata(vendor="TestCo", date="2025-03", document_type=DocumentType.INVOICE)

    archive_root = Path("/archive")
    path = get_archive_path(archive_root, meta, override="{year}/receipts")

    assert path == Path("/archive/2025/receipts")


def test_rule_matching_doc_type():
    """Test archive rule matching by document type."""
    rules = [ArchiveRule(doc_type="Tax_Form", path="{year}/tax-documents")]

    meta = DocumentMetadata(vendor="IRS", date="2025-01", document_type=DocumentType.TAX_FORM)

    matched_path = match_archive_rules(meta, rules)
    assert matched_path == "{year}/tax-documents"


def test_rule_matching_vendor():
    """Test archive rule matching by vendor substring."""
    rules = [ArchiveRule(vendor_contains="ComEd", path="{year}/utilities")]

    meta = DocumentMetadata(vendor="ComEd Company", date="2025-01", document_type=DocumentType.BILL)

    matched_path = match_archive_rules(meta, rules)
    assert matched_path == "{year}/utilities"


def test_rule_matching_combined():
    """Test archive rule matching with multiple criteria."""
    rules = [
        ArchiveRule(doc_type="Receipt", vendor_contains="Medical", path="{year}/medical")
    ]

    # Should match
    meta1 = DocumentMetadata(
        vendor="Medical Center", date="2025-01", document_type=DocumentType.RECEIPT
    )
    assert match_archive_rules(meta1, rules) == "{year}/medical"

    # Should not match (wrong doc type)
    meta2 = DocumentMetadata(
        vendor="Medical Center", date="2025-01", document_type=DocumentType.BILL
    )
    assert match_archive_rules(meta2, rules) is None

    # Should not match (wrong vendor)
    meta3 = DocumentMetadata(vendor="Store", date="2025-01", document_type=DocumentType.RECEIPT)
    assert match_archive_rules(meta3, rules) is None


def test_rule_priority():
    """Test that first matching rule wins."""
    rules = [
        ArchiveRule(doc_type="Tax_Form", path="{year}/tax-documents"),
        ArchiveRule(doc_type="Tax_Form", path="{year}/other"),  # Should not be used
    ]

    meta = DocumentMetadata(vendor="IRS", date="2025-01", document_type=DocumentType.TAX_FORM)

    matched_path = match_archive_rules(meta, rules)
    assert matched_path == "{year}/tax-documents"


def test_no_rule_match():
    """Test default behavior when no rules match."""
    rules = [ArchiveRule(doc_type="Tax_Form", path="{year}/tax-documents")]

    meta = DocumentMetadata(vendor="TestCo", date="2025-01", document_type=DocumentType.INVOICE)

    matched_path = match_archive_rules(meta, rules)
    assert matched_path is None

    # Should fall back to default YYYY/MM
    archive_root = Path("/archive")
    path = get_archive_path(archive_root, meta, rules=rules)
    assert path == Path("/archive/2025/01")


def test_override_precedence_over_rules():
    """Test that manual override takes precedence over rules."""
    rules = [ArchiveRule(doc_type="Tax_Form", path="{year}/tax-documents")]

    meta = DocumentMetadata(vendor="IRS", date="2025-01", document_type=DocumentType.TAX_FORM)

    archive_root = Path("/archive")
    path = get_archive_path(archive_root, meta, override="2025/custom", rules=rules)

    # Override should win
    assert path == Path("/archive/2025/custom")
