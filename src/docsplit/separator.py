"""Generate separator sheets for batch scanning."""

import logging
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def create_separator_sheet(output_path: Path, separator_text: str = "DOCPROC_SEP") -> None:
    """
    Generate a separator sheet PDF.

    Args:
        output_path: Where to save the PDF
        separator_text: Text to print on separator
    """
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter size (8.5 x 11 inches)

    # Title
    title_rect = fitz.Rect(50, 100, 562, 150)
    page.insert_textbox(
        title_rect,
        "DOCUMENT SEPARATOR",
        fontsize=36,
        fontname="helv",
        align=fitz.TEXT_ALIGN_CENTER,
    )

    # Instructions
    instructions = """
Place this sheet between documents when batch scanning.

The text below will be detected automatically and used to split
the scanned PDF into individual documents.

Print multiple copies and keep them near your scanner.
    """
    inst_rect = fitz.Rect(50, 180, 562, 300)
    page.insert_textbox(
        inst_rect,
        instructions.strip(),
        fontsize=14,
        fontname="helv",
        align=fitz.TEXT_ALIGN_CENTER,
    )

    # Separator code (large, clear text for OCR)
    code_rect = fitz.Rect(50, 350, 562, 450)
    page.insert_textbox(
        code_rect,
        separator_text,
        fontsize=48,
        fontname="helv",
        align=fitz.TEXT_ALIGN_CENTER,
    )

    # Visual separator
    page.draw_line(fitz.Point(100, 500), fitz.Point(512, 500), width=2)

    # Barcode-style representation
    barcode_text = f"|||  {separator_text}  |||"
    barcode_rect = fitz.Rect(50, 520, 562, 580)
    page.insert_textbox(
        barcode_rect,
        barcode_text,
        fontsize=24,
        fontname="cour",  # Monospace
        align=fitz.TEXT_ALIGN_CENTER,
    )

    # Footer
    footer_rect = fitz.Rect(50, 700, 562, 750)
    page.insert_textbox(
        footer_rect,
        "docsplit separator sheet - do not write on this page",
        fontsize=10,
        fontname="helv",
        align=fitz.TEXT_ALIGN_CENTER,
        color=(0.5, 0.5, 0.5),
    )

    # Save
    doc.save(output_path)
    doc.close()
    logger.info(f"Separator sheet created: {output_path}")
