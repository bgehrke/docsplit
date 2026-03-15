"""PDF splitting and separator detection."""

import logging
from pathlib import Path

import fitz  # PyMuPDF
from rapidfuzz import fuzz

from .config import Config
from .ocr import ocr_all_pages

logger = logging.getLogger(__name__)


def is_separator_page(text: str, separator_text: str, threshold: int = 85) -> bool:
    """
    Check if page text matches separator marker using fuzzy matching.

    Args:
        text: OCR text from the page
        separator_text: Expected separator text
        threshold: Fuzzy match score threshold (0-100)

    Returns:
        True if this appears to be a separator page
    """
    if not text:
        return False

    # Use partial ratio for fuzzy matching
    score = fuzz.partial_ratio(separator_text.upper(), text.upper())
    return score >= threshold


def split_pdf_on_separators(
    pdf_path: Path, output_dir: Path, config: Config
) -> list[Path]:
    """
    Split a PDF into multiple documents at separator pages.

    Args:
        pdf_path: Path to input PDF
        output_dir: Directory to save split documents
        config: Application configuration

    Returns:
        List of paths to split documents
    """
    logger.info(f"Processing {pdf_path.name} for separator detection...")

    # OCR all pages
    page_texts = ocr_all_pages(pdf_path, config.ocr)
    total_pages = len(page_texts)

    if total_pages == 0:
        logger.error("No pages found or OCR failed completely")
        return []

    logger.info(f"Found {total_pages} pages, detecting separators...")

    # Find separator page indices
    separator_indices = []
    for i, text in enumerate(page_texts):
        if is_separator_page(text, config.separator.text, config.separator.fuzzy_threshold):
            separator_indices.append(i)
            logger.info(f"  Page {i + 1}: SEPARATOR")
        else:
            logger.debug(f"  Page {i + 1}: content ({len(text)} chars)")

    if not separator_indices:
        logger.warning("No separator pages found. Processing as single document.")
        # Copy the original as the only document
        output_path = output_dir / f"document_001.pdf"
        import shutil

        shutil.copy(pdf_path, output_path)
        return [output_path]

    logger.info(f"Found {len(separator_indices)} separator page(s)")

    # Open PDF for splitting
    pdf_doc = fitz.open(pdf_path)

    # Calculate document boundaries
    # Documents are between separators (or start/end of file)
    documents = []
    doc_start = 0

    for sep_idx in separator_indices:
        if sep_idx > doc_start:
            # There are pages before this separator
            documents.append((doc_start, sep_idx - 1))
        
        # Skip the separator page
        doc_start = sep_idx + 1
        
        # If duplex scanning, the next page might be the blank back of separator
        # Check if it's blank and skip it too
        if doc_start < total_pages:
            next_page_text = page_texts[doc_start]
            if len(next_page_text.strip()) < 100:  # Blank page threshold
                logger.debug(f"  Skipping blank back of separator (page {doc_start + 1})")
                doc_start += 1

    # Don't forget pages after the last separator
    if doc_start < total_pages:
        documents.append((doc_start, total_pages - 1))

    logger.info(f"Splitting into {len(documents)} document(s)")

    # Extract each document
    output_paths = []
    for i, (start, end) in enumerate(documents, 1):
        output_path = output_dir / f"document_{i:03d}.pdf"

        # Create new PDF with just these pages
        new_doc = fitz.open()
        new_doc.insert_pdf(pdf_doc, from_page=start, to_page=end)
        new_doc.save(output_path)
        new_doc.close()

        page_count = end - start + 1
        logger.info(
            f"  Document {i}: pages {start + 1}-{end + 1} "
            f"({page_count} page(s)) -> {output_path.name}"
        )

        output_paths.append(output_path)

    pdf_doc.close()
    return output_paths


def get_page_count(pdf_path: Path) -> int:
    """Get the number of pages in a PDF."""
    try:
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except Exception as e:
        logger.error(f"Failed to get page count for {pdf_path}: {e}")
        return 0
