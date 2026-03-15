"""Tests for scanner module."""

from docsplit.scanner import is_separator_page


def test_is_separator_page_exact_match():
    """Test separator detection with exact match."""
    text = "DOCPROC_SEP"
    assert is_separator_page(text, "DOCPROC_SEP", threshold=85)


def test_is_separator_page_fuzzy_match():
    """Test separator detection with OCR errors."""
    # Common OCR mistakes
    text = "D0CPR0C_SEP"  # O -> 0
    assert is_separator_page(text, "DOCPROC_SEP", threshold=75)

    text = "DOCPR0C_5EP"  # O -> 0, S -> 5
    assert is_separator_page(text, "DOCPROC_SEP", threshold=70)


def test_is_separator_page_case_insensitive():
    """Test separator detection is case insensitive."""
    text = "docproc_sep"
    assert is_separator_page(text, "DOCPROC_SEP", threshold=85)


def test_is_separator_page_embedded_in_text():
    """Test separator detection when embedded in other text."""
    text = "Some random text DOCPROC_SEP more text"
    assert is_separator_page(text, "DOCPROC_SEP", threshold=85)


def test_is_separator_page_no_match():
    """Test separator detection with completely different text."""
    text = "This is a normal document page"
    assert not is_separator_page(text, "DOCPROC_SEP", threshold=85)
