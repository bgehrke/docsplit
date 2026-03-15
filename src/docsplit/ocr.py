"""OCR functionality."""

import logging
from pathlib import Path
from typing import Optional

import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from .config import OCRConfig
from .preprocessing import preprocess_for_ocr

logger = logging.getLogger(__name__)


def ocr_image(image: Image.Image, config: OCRConfig) -> str:
    """Run OCR on a PIL image."""
    try:
        # Apply preprocessing if enabled
        if config.preprocessing:
            image = preprocess_for_ocr(
                image,
                deskew_enabled=config.deskew,
                sharpen_enabled=config.sharpen,
                contrast_enabled=config.contrast,
                denoise_enabled=config.denoise,
            )

        text = pytesseract.image_to_string(image, lang=config.language)
        return text.strip()
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""


def ocr_pdf_pages(
    pdf_path: Path, config: OCRConfig, first_page: int = 1, last_page: Optional[int] = None
) -> str:
    """
    OCR specific pages from a PDF.

    Args:
        pdf_path: Path to PDF file
        config: OCR configuration
        first_page: First page number (1-indexed)
        last_page: Last page number (None = use max_pages from config)

    Returns:
        Concatenated OCR text from all pages
    """
    if last_page is None:
        last_page = first_page + config.max_pages - 1

    logger.debug(
        f"Converting PDF pages {first_page}-{last_page} to images (DPI={config.dpi})..."
    )

    try:
        images = convert_from_path(
            pdf_path, dpi=config.dpi, first_page=first_page, last_page=last_page
        )
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        return ""

    logger.debug(f"OCR-ing {len(images)} page(s)...")

    text_parts = []
    for i, image in enumerate(images, start=first_page):
        page_text = ocr_image(image, config)
        if page_text:
            text_parts.append(f"--- Page {i} ---\n{page_text}")

    return "\n".join(text_parts)


def ocr_all_pages(pdf_path: Path, config: OCRConfig) -> list[str]:
    """
    OCR all pages of a PDF, returning text for each page separately.

    Returns:
        List of OCR text (one per page)
    """
    logger.debug(f"Converting entire PDF to images (DPI={config.dpi})...")

    try:
        images = convert_from_path(pdf_path, dpi=config.dpi)
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        return []

    logger.debug(f"OCR-ing {len(images)} page(s)...")

    texts = []
    for i, image in enumerate(images, start=1):
        page_text = ocr_image(image, config)
        texts.append(page_text)
        logger.debug(f"  Page {i}: {len(page_text)} chars")

    return texts
