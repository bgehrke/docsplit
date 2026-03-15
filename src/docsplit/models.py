"""Data models for docsplit."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    """Standard document types."""

    INVOICE = "Invoice"
    STATEMENT = "Statement"
    BILL = "Bill"
    LETTER = "Letter"
    RECEIPT = "Receipt"
    NOTICE = "Notice"
    TAX_FORM = "Tax_Form"
    PROPOSAL = "Proposal"
    CONTRACT = "Contract"
    REPORT = "Report"
    FORM = "Form"
    OTHER = "Other"


class ProcessingStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    QUARANTINE = "quarantine"


class DocumentMetadata(BaseModel):
    """Metadata extracted from a document."""

    vendor: str = Field(default="Unknown", description="Company/vendor name (short form)")
    date: Optional[str] = Field(
        default=None, description="Document date (YYYY-MM-DD or YYYY-MM)"
    )
    document_type: DocumentType = Field(default=DocumentType.OTHER)
    tax_form_id: Optional[str] = Field(
        default=None, description="Tax form identifier (e.g., W-2, 1099-DIV, 1098)"
    )

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format (YYYY-MM-DD or YYYY-MM)."""
        if v is None or v.upper() == "UNKNOWN":
            return None

        # Accept YYYY-MM-DD or YYYY-MM
        import re

        if re.match(r"^\d{4}-\d{2}(-\d{2})?$", v):
            return v

        return None


class Document(BaseModel):
    """A processed document."""

    id: Optional[int] = None
    batch_id: Optional[int] = None
    source_path: Path
    source_page_range: Optional[str] = None  # e.g., "5-8"
    archive_path: Optional[Path] = None
    metadata: DocumentMetadata
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Batch(BaseModel):
    """A batch of scanned documents."""

    id: Optional[int] = None
    source_path: Path
    processed_at: datetime = Field(default_factory=datetime.now)
    total_docs: int = 0
    success_count: int = 0
    error_count: int = 0


# Document type abbreviations for filenames
TYPE_ABBREVIATIONS = {
    DocumentType.INVOICE: "Inv",
    DocumentType.STATEMENT: "Stmt",
    DocumentType.BILL: "Bill",
    DocumentType.LETTER: "Ltr",
    DocumentType.RECEIPT: "Rcpt",
    DocumentType.NOTICE: "Notice",
    DocumentType.TAX_FORM: "Tax",
    DocumentType.PROPOSAL: "Prop",
    DocumentType.CONTRACT: "Contract",
    DocumentType.REPORT: "Rpt",
    DocumentType.FORM: "Form",
    DocumentType.OTHER: "Doc",
}
