"""Metadata extraction using LLM."""

import json
import logging
from pathlib import Path
from typing import Tuple

import ollama
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import Config
from .models import DocumentMetadata, DocumentType
from .ocr import ocr_pdf_pages

logger = logging.getLogger(__name__)


def normalize_tax_form_id(tax_form_id: str | None) -> str | None:
    """
    Normalize tax form ID format.
    
    Examples:
        "W-2" -> "W2"
        "1099-DIV" -> "1099DIV"
        "1099 INT" -> "1099INT"
    
    Args:
        tax_form_id: Raw tax form ID from LLM
        
    Returns:
        Normalized tax form ID (no hyphens or spaces)
    """
    if not tax_form_id:
        return None
    
    # Remove hyphens and spaces, uppercase
    normalized = tax_form_id.replace("-", "").replace(" ", "").upper()
    
    return normalized if normalized else None

METADATA_PROMPT_TEMPLATE = """You are analyzing a scanned document to extract metadata.

Return a JSON object with these fields:
{{
  "vendor": "short company name (2-3 words max)",
  "date": "YYYY-MM-DD or YYYY-MM if only month is clear",
  "document_type": "one of: Invoice, Statement, Bill, Letter, Receipt, Notice, Tax_Form, Proposal, Contract, Report, Form, Other",
  "tax_form_id": "tax form type if this is a tax document (e.g., W-2, 1099-DIV, 1099-INT, 1098, etc.)"
}}

Rules:
- vendor: Use SHORT name. Examples:
  - "The Huntington National Bank" → "Huntington Bank"
  - "Farmer, Poklop, Hoppa & Co." → "Farmer Poklop"
  - "Northwest Community Healthcare" → "Northwest Healthcare"
  Drop words like "The", "LLC", "Inc", "Corp", "& Co", "Company".
- date: The document date (NOT today's date). If you can only determine the month, use YYYY-MM-01.
  Use null if unclear.
- document_type: MUST be one of the exact types listed above
- tax_form_id: If this is a tax form (W-2, 1099, 1098, etc.), extract the form type (e.g., "W-2", "1099-DIV", "1099-INT", "1098").
  Remove spaces and hyphens for consistency (e.g., "W2", "1099DIV", "1099INT").
  Use null if not a tax form.

Document text (first pages):
---
{ocr_text}
---

Return ONLY the JSON object, no other text."""


def calculate_confidence(metadata: DocumentMetadata, response_text: str) -> float:
    """
    Calculate confidence score for extracted metadata.

    Returns:
        Score from 0.0 to 1.0
    """
    score = 0.0

    # Vendor confidence
    if metadata.vendor and metadata.vendor != "Unknown":
        score += 0.4
        # Bonus if vendor is reasonably long
        if len(metadata.vendor) >= 5:
            score += 0.1

    # Date confidence
    if metadata.date:
        score += 0.3
        # Full date is more confident than month-only
        if len(metadata.date) == 10:  # YYYY-MM-DD
            score += 0.1

    # Document type confidence
    if metadata.document_type != DocumentType.OTHER:
        score += 0.2

    return min(score, 1.0)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def extract_metadata_from_text(text: str, config: Config) -> Tuple[DocumentMetadata, float]:
    """
    Extract metadata from OCR text using LLM.

    Args:
        text: OCR text from document
        config: Application configuration

    Returns:
        Tuple of (metadata, confidence_score)
    """
    if len(text.strip()) < 50:
        logger.warning("Very little text available for metadata extraction")
        return DocumentMetadata(), 0.0

    # Truncate text to avoid token limits
    truncated_text = text[:4000]

    prompt = METADATA_PROMPT_TEMPLATE.format(ocr_text=truncated_text)

    try:
        logger.debug(f"Calling LLM ({config.metadata.model})...")
        response = ollama.chat(
            model=config.metadata.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": config.metadata.temperature},
        )

        result_text = response["message"]["content"].strip()
        logger.debug(f"LLM response: {result_text[:200]}...")

        # Try to extract JSON from response
        # Sometimes LLMs wrap JSON in markdown code blocks
        if "```json" in result_text:
            json_start = result_text.find("```json") + 7
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()
        elif "```" in result_text:
            json_start = result_text.find("```") + 3
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()

        # Parse JSON
        data = json.loads(result_text)

        # Normalize document_type to enum
        if "document_type" in data:
            doc_type_str = data["document_type"].replace(" ", "_").upper()
            try:
                data["document_type"] = DocumentType[doc_type_str]
            except KeyError:
                logger.warning(f"Unknown document type: {data['document_type']}, using OTHER")
                data["document_type"] = DocumentType.OTHER

        # Normalize tax_form_id
        if "tax_form_id" in data and data["tax_form_id"]:
            data["tax_form_id"] = normalize_tax_form_id(data["tax_form_id"])
        
        metadata = DocumentMetadata(**data)
        confidence = calculate_confidence(metadata, result_text)
        logger.info(f"Extracted metadata: {metadata.model_dump_json()}")
        logger.info(f"Confidence score: {confidence:.2f}")
        return metadata, confidence

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        logger.debug(f"Raw response: {result_text}")
        return DocumentMetadata(), 0.0

    except ValidationError as e:
        logger.error(f"Metadata validation failed: {e}")
        return DocumentMetadata(), 0.0

    except Exception as e:
        logger.error(f"LLM metadata extraction failed: {e}")
        raise  # Let retry decorator handle this


def extract_metadata(pdf_path: Path, config: Config) -> Tuple[DocumentMetadata, float]:
    """
    Extract metadata from a PDF document.

    Args:
        pdf_path: Path to PDF file
        config: Application configuration

    Returns:
        Tuple of (metadata, confidence_score)
    """
    logger.info(f"Extracting metadata from {pdf_path.name}...")

    # OCR first N pages
    ocr_text = ocr_pdf_pages(pdf_path, config.ocr, first_page=1, last_page=config.ocr.max_pages)

    if not ocr_text:
        logger.warning(f"No OCR text extracted from {pdf_path.name}")
        return DocumentMetadata(), 0.0

    try:
        return extract_metadata_from_text(ocr_text, config)
    except Exception as e:
        logger.error(f"Metadata extraction failed after retries: {e}")
        return DocumentMetadata(), 0.0
