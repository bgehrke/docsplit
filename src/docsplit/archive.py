"""Archive file organization and naming."""

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

from .config import Config
from .models import TYPE_ABBREVIATIONS, DocumentMetadata

logger = logging.getLogger(__name__)

# Words to strip from vendor names
FILLER_WORDS = {
    "the",
    "llc",
    "inc",
    "corp",
    "corporation",
    "company",
    "co",
    "ltd",
    "limited",
    "plc",
    "&",
}


def strip_filler_words(text: str) -> str:
    """Remove common filler words from vendor names."""
    words = text.split()
    filtered = []

    for word in words:
        # Check if word (lowercase, no punctuation) is a filler word
        word_clean = word.lower().strip(".,")
        if word_clean and word_clean not in FILLER_WORDS:
            filtered.append(word)

    return " ".join(filtered) if filtered else text


def sanitize_filename(text: str) -> str:
    """Convert text to a safe filename component."""
    # Replace spaces and special chars with underscores
    text = re.sub(r"[^\w\-]", "_", text)
    # Remove multiple consecutive underscores
    text = re.sub(r"_+", "_", text)
    # Remove leading/trailing underscores
    text = text.strip("_")
    return text if text else "Unknown"


def generate_filename(metadata: DocumentMetadata, template: str | None = None) -> str:
    """
    Generate filename from metadata.

    Default format: YYYY-MM_Vendor_Type.pdf
    Custom format via template (e.g., "{tax_form_id}-{vendor}.pdf")

    Args:
        metadata: Document metadata
        template: Optional naming template with variables

    Returns:
        Filename (including .pdf extension)
    """
    # If custom template provided, use it
    if template:
        # Available variables
        variables = {
            "tax_form_id": metadata.tax_form_id or "Unknown",
            "vendor": strip_filler_words(metadata.vendor),
            "year": metadata.date[:4] if metadata.date and len(metadata.date) >= 4 else str(datetime.now().year),
            "month": metadata.date[5:7] if metadata.date and len(metadata.date) >= 7 else f"{datetime.now().month:02d}",
            "type": TYPE_ABBREVIATIONS.get(metadata.document_type, "Doc"),
        }
        
        # Sanitize all variables
        variables = {k: sanitize_filename(str(v)) for k, v in variables.items()}
        
        try:
            filename = template.format(**variables)
            # Ensure .pdf extension
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            return filename
        except KeyError as e:
            logger.warning(f"Invalid template variable {e}, falling back to default naming")
    
    # Default naming
    # Handle date
    date = metadata.date
    if not date or not re.match(r"^\d{4}-\d{2}", date):
        # Use current year-month if date is invalid
        date = datetime.now().strftime("%Y-%m")
        logger.warning(f"Invalid or missing date, using current: {date}")
    elif len(date) == 10:  # YYYY-MM-DD -> YYYY-MM
        date = date[:7]

    # Clean up vendor name
    vendor = strip_filler_words(metadata.vendor)
    vendor = sanitize_filename(vendor)
    vendor = vendor[:30]  # Limit length

    # Get abbreviated document type
    doc_type = TYPE_ABBREVIATIONS.get(metadata.document_type, "Doc")
    doc_type = sanitize_filename(doc_type)

    return f"{date}_{vendor}_{doc_type}.pdf"


def match_archive_rules(metadata: DocumentMetadata, rules: list) -> tuple[str | None, str | None]:
    """
    Check if metadata matches any archive rules.

    Args:
        metadata: Document metadata
        rules: List of ArchiveRule objects

    Returns:
        Tuple of (path_template, naming_template) if matched, (None, None) otherwise
    """
    for rule in rules:
        # Check document type match
        # Special case: if rule is for Tax_Form, also match if document has tax_form_id
        if rule.doc_type:
            if rule.doc_type == "Tax_Form":
                # Match if either classified as Tax_Form OR has a tax_form_id
                if metadata.document_type.value != "Tax_Form" and not metadata.tax_form_id:
                    continue
            elif rule.doc_type != metadata.document_type.value:
                continue

        # Check vendor substring match
        if rule.vendor_contains and rule.vendor_contains.lower() not in metadata.vendor.lower():
            continue

        # Rule matched
        logger.info(f"Archive rule matched: {rule.path}")
        return rule.path, rule.naming_template

    return None, None


def get_archive_path(
    archive_root: Path,
    metadata: DocumentMetadata,
    override: str | None = None,
    rules: list | None = None,
) -> Path:
    """
    Determine the archive directory path.

    Default structure: Archive/YYYY/MM/
    Can be overridden via rules or manual override.

    Args:
        archive_root: Root archive directory
        metadata: Document metadata
        override: Manual path override (e.g., "2025/tax-documents")
        rules: Archive routing rules

    Returns:
        Directory path (without filename)
    """
    date = metadata.date

    # Parse year and month from date
    try:
        if date and re.match(r"^\d{4}-\d{2}", date):
            year = date[:4]
            month = date[5:7]
        else:
            # Use current date if invalid
            now = datetime.now()
            year = str(now.year)
            month = f"{now.month:02d}"
    except Exception:
        now = datetime.now()
        year = str(now.year)
        month = f"{now.month:02d}"

    # Check for manual override first
    if override:
        # Support template variables
        path_template = override.format(year=year, month=month)
        logger.info(f"Using manual path override: {path_template}")
        return archive_root / path_template

    # Check archive rules
    if rules:
        rule_path, _ = match_archive_rules(metadata, rules)
        if rule_path:
            path_template = rule_path.format(year=year, month=month)
            return archive_root / path_template

    # Default: YYYY/MM
    return archive_root / year / month


def resolve_filename_collision(filepath: Path) -> Path:
    """
    If file exists, append _001, _002, etc.

    Args:
        filepath: Desired file path

    Returns:
        Available file path (may be modified)
    """
    if not filepath.exists():
        return filepath

    base = filepath.stem
    suffix = filepath.suffix
    parent = filepath.parent

    counter = 1
    while True:
        new_name = f"{base}_{counter:03d}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1
        if counter > 999:
            raise RuntimeError(f"Too many filename collisions for {filepath}")


def archive_document(
    source_path: Path,
    metadata: DocumentMetadata,
    config: Config,
    dry_run: bool = False,
    dest_override: str | None = None,
) -> Path:
    """
    Move document to archive with proper naming.

    Args:
        source_path: Source PDF file
        metadata: Document metadata
        config: Application configuration
        dry_run: If True, don't actually move the file
        dest_override: Manual destination path override

    Returns:
        Final archive path

    Raises:
        OSError: If file operations fail
    """
    # Check for custom naming template from rules (apply even with dest override)
    naming_template = None
    if config.archive_rules:
        _, naming_template = match_archive_rules(metadata, config.archive_rules)
    
    # Generate filename and path
    filename = generate_filename(metadata, template=naming_template)
    archive_dir = get_archive_path(
        config.paths.archive, metadata, override=dest_override, rules=config.archive_rules
    )
    dest_path = archive_dir / filename
    dest_path = resolve_filename_collision(dest_path)

    if dry_run:
        logger.info(f"[DRY RUN] Would move {source_path.name} to {dest_path}")
        return dest_path

    # Create directory structure
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Move file
    shutil.move(str(source_path), str(dest_path))
    logger.info(f"Archived: {dest_path}")

    return dest_path
