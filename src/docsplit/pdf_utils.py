"""PDF utility functions."""

import logging
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def is_blank_page(page: fitz.Page, threshold: int = 100) -> bool:
    """
    Detect if a PDF page is blank or nearly blank.

    Args:
        page: PyMuPDF page object
        threshold: Maximum number of characters to consider blank

    Returns:
        True if page appears blank
    """
    # Get text from page
    text = page.get_text().strip()

    # Check character count
    if len(text) < threshold:
        return True

    return False


def remove_trailing_blank_pages(pdf_path: Path) -> Path:
    """
    Remove trailing blank pages from a PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Path to cleaned PDF (same path, modified in place)
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    if total_pages == 0:
        doc.close()
        return pdf_path

    # Check pages from end, find first non-blank
    last_content_page = total_pages - 1

    for i in range(total_pages - 1, -1, -1):
        page = doc[i]
        if not is_blank_page(page):
            last_content_page = i
            break

    # If we found blank pages at the end
    if last_content_page < total_pages - 1:
        blank_count = total_pages - last_content_page - 1
        logger.info(f"Removing {blank_count} trailing blank page(s)")

        # Create new doc with only content pages
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=0, to_page=last_content_page)
        doc.close()

        # Save back to same file
        new_doc.save(pdf_path)
        new_doc.close()
    else:
        doc.close()

    return pdf_path
