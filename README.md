# docsplit

Automated document splitting and archival from batch scans.

## What It Does

1. **Splits batch-scanned PDFs** at separator pages (print separator sheets, scan everything together)
2. **Extracts metadata** using OCR + LLM (vendor, date, document type)
3. **Organizes into archive** with smart naming: `YYYY-MM_Vendor_Type.pdf` filed into `Archive/YYYY/MM/`
4. **Watch folder automation** - drop PDFs in Inbox, get organized documents out

## Quick Start

### Installation

```bash
# Install dependencies
poetry install

# Or with pip
pip install -e .
```

### Configuration

Copy the example config and edit paths:

```bash
cp config.example.yaml ~/.config/docsplit/config.yaml
```

Edit `~/.config/docsplit/config.yaml` with your paths.

### Usage

**Watch mode (recommended):**
```bash
docsplit watch
```

Drop batch-scanned PDFs into your inbox folder. They'll be processed automatically.

**Single file:**
```bash
docsplit process /path/to/scanned.pdf
```

**Generate separator sheets:**
```bash
docsplit separator
```

**Search documents:**
```bash
docsplit search --vendor "Huntington" --year 2025
```

**Web UI:**
```bash
docsplit web
```
Then open http://localhost:5000 in your browser.

**Reprocess failed documents:**
```bash
docsplit reprocess --failed
```

Print multiple copies and keep them near your scanner. Insert one between each document when batch scanning.

## How It Works

1. **Print separator sheets** - Run `docsplit separator` to generate a PDF with a barcode/marker
2. **Batch scan** - Stack your documents with separators between them, scan to one PDF
3. **Drop in inbox** - Save the scanned PDF to your inbox folder
4. **Automatic processing**:
   - Detects separator pages (fuzzy matching, handles OCR errors)
   - Splits into individual documents
   - OCRs first 1-2 pages
   - Sends to LLM for metadata extraction (vendor, date, type)
   - Generates clean filename
   - Files into `Archive/YYYY/MM/`
   - Moves original to `Processed/`

## Architecture

```
docsplit/
├── src/docsplit/
│   ├── scanner.py      # PDF splitting, separator detection
│   ├── ocr.py          # OCR pipeline (Tesseract)
│   ├── metadata.py     # LLM extraction
│   ├── archive.py      # File organization
│   ├── database.py     # SQLite tracking
│   ├── watcher.py      # Inbox monitoring
│   ├── config.py       # Config management
│   ├── models.py       # Pydantic models
│   └── cli.py          # Command-line interface
└── tests/              # Test suite
```

## Configuration

Edit `~/.config/docsplit/config.yaml`:

```yaml
paths:
  inbox: /Volumes/DataDrive/Archive/Inbox-scans
  archive: /Volumes/DataDrive/Archive
  processed: /Volumes/DataDrive/Archive/Processed
  quarantine: /Volumes/DataDrive/Archive/Quarantine
  database: /Volumes/DataDrive/Archive/.docsplit.db

ocr:
  dpi: 150
  language: eng

metadata:
  model: mistral
  temperature: 0.1

separator:
  text: DOCPROC_SEP
  fuzzy_threshold: 85

watch:
  interval: 5
  stability_check: true
```

## Development

```bash
# Install with dev dependencies
poetry install

# Run tests
poetry run pytest

# Type checking
poetry run mypy src/docsplit

# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/ tests/
```

## Requirements

- Python 3.12+
- Tesseract OCR (`brew install tesseract` on macOS)
- Poppler (`brew install poppler` on macOS)
- Ollama with a model installed (`ollama pull mistral`)

## License

MIT
