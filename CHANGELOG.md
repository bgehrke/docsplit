# Changelog

## [0.2.0] - 2026-03-15 (Phase 2)

### Features

- **OCR Preprocessing**: Image enhancement for better accuracy
  - Deskewing (correct rotation)
  - Sharpening (improve text clarity)
  - Contrast enhancement (CLAHE)
  - Noise removal (optional, slow)
- **Retry Logic**: Automatic retry with exponential backoff for LLM failures
- **Confidence Scoring**: Track metadata extraction confidence (0.0-1.0)
- **Web UI**: Simple Flask-based search interface
- **Bulk Reprocessing**: Reprocess failed documents or entire batches

### Testing

- **20 tests** passing
- **60% code coverage**
- Tests for models, archive, database, scanner, metadata

### Commands Added

```bash
# Start web UI
docsplit web

# Reprocess failed documents
docsplit reprocess --failed

# Reprocess specific batch
docsplit reprocess --batch-id 5
```

### Dependencies Added

- opencv-python (image preprocessing)
- numpy (image operations)
- tenacity (retry logic)
- flask (web UI)

## [0.1.0] - 2026-03-15 (Phase 1)

### Initial Release

**Complete rebuild from scratch** based on the original `docproc` prototype.

#### Core Features

- **PDF Splitting**: Detect separator pages using fuzzy OCR matching (handles OCR errors)
- **Metadata Extraction**: LLM-based (Ollama) with structured JSON output
- **Smart Archiving**: Files documents into `YYYY/MM/` structure with clean naming
- **Watch Mode**: Automated processing of inbox folder
- **SQLite Database**: Full audit trail and search capability
- **Error Handling**: Quarantine folder for failed documents

#### Architecture Improvements

- Modular codebase (separate modules for scanner, OCR, metadata, archive, database)
- Type hints throughout (Python 3.12+)
- Pydantic models for data validation
- Poetry for dependency management
- Test suite with pytest
- Config file support (YAML)
- CLI with multiple subcommands

#### What Changed from `docproc`

**Better:**
- Fuzzy separator matching (tolerates OCR errors)
- JSON-structured LLM output (more reliable than text parsing)
- Month-level date accuracy (no forced day precision)
- SQLite database for tracking and search
- Modular code (easy to maintain and extend)
- Tests (pytest + coverage)
- Config file (no hardcoded paths)
- Quarantine folder for failures
- Better error handling

**Same:**
- Separator-based splitting approach
- OCR + LLM workflow
- `YYYY/MM/` archive structure
- Watch folder automation

#### Commands

```bash
# Process a single PDF
docsplit process /path/to/scanned.pdf

# Watch inbox folder
docsplit watch

# Generate separator sheets
docsplit separator

# Search archived documents
docsplit search --vendor "Huntington" --year 2025
```

#### Configuration

Config file at `~/.config/docsplit/config.yaml` with paths, OCR settings, LLM model, etc.

#### Dependencies

- Python 3.12+
- PyMuPDF (PDF manipulation)
- Tesseract (OCR)
- Ollama (local LLM)
- Pydantic (data validation)
- Poetry (dependency management)
