## Implementation Notes

Built by Fitz on 2026-03-15 for Brian Gehrke.

### What This Is

A complete rebuild of the original `docproc` prototype with:
- Clean architecture
- Tests
- Better error handling
- Database tracking
- Modular design

### Design Decisions

#### 1. **Fuzzy Separator Matching**

Problem: OCR sometimes misreads "DOCPROC_SEP" as "D0CPR0C_5EP" or similar.

Solution: Use `rapidfuzz` library with 85% threshold. If OCR text is 85%+ similar to separator text, treat as separator.

#### 2. **JSON-Structured LLM Output**

Problem: Original used freeform text parsing (`VENDOR: ...`), which is brittle.

Solution: Prompt LLM to return JSON object. Parse with `json.loads()` and validate with Pydantic. More reliable.

#### 3. **Month-Level Dates**

Problem: Forcing exact dates (YYYY-MM-DD) causes failures when only month is clear.

Solution: Accept both YYYY-MM and YYYY-MM-DD. Filename uses YYYY-MM format. Archive folders use YYYY/MM/.

#### 4. **SQLite Database**

Why: Enables search, audit trail, and debugging without parsing filesystem.

Tables:
- `batches`: Track each batch PDF processed
- `documents`: Track each extracted document with metadata, status, errors

#### 5. **Modular Architecture**

Files:
- `scanner.py`: PDF splitting logic
- `ocr.py`: OCR operations
- `metadata.py`: LLM extraction
- `archive.py`: File organization
- `database.py`: SQLite operations
- `watcher.py`: Inbox monitoring
- `cli.py`: Command-line interface
- `config.py`: Configuration loading
- `models.py`: Data models (Pydantic)
- `separator.py`: Separator sheet generation

Why: Each module has one job. Easy to test, easy to modify.

#### 6. **Poetry vs pip**

Choice: Poetry

Reasons:
- Lock file for reproducible builds
- Better dependency resolution
- Dev dependencies separate from runtime
- Modern, clean workflow

### Testing Strategy

**Current coverage: ~18%** (7 tests passing)

Tests focus on:
- Data models (validation, defaults)
- Filename generation
- Sanitization logic

**Not yet tested:**
- OCR (requires sample PDFs)
- LLM extraction (requires mocked ollama)
- Scanner splitting (requires test PDFs)
- Database operations

**Next steps for testing:**
- Create fixture PDFs with known content
- Mock ollama responses
- Test full end-to-end workflow

### Configuration

User creates `~/.config/docsplit/config.yaml` with:
- Paths (inbox, archive, processed, quarantine, database)
- OCR settings (DPI, language)
- LLM settings (model, temperature)
- Separator settings (text, fuzzy threshold)
- Watch settings (interval, stability check)

### Error Handling

**Quarantine folder**: Failed documents moved here with error log.

**Status tracking**: Every document gets a status (pending, success, failed, quarantine) in the database.

**Graceful degradation**: If metadata extraction fails, use defaults ("Unknown" vendor, current date).

### Future Enhancements (Not Implemented)

**Phase 2:**
- OCR preprocessing (deskew, sharpen, contrast adjustment)
- Retry logic for transient failures
- Confidence scoring for metadata
- Web UI for manual review
- Bulk re-processing

**Phase 3:**
- Multiple separator types (QR codes, barcodes)
- Multi-language OCR
- Cloud storage backends (S3, Google Drive)
- Email ingestion (forward scans to an email address)

### Performance Notes

**Current bottleneck**: OCR is slow (~2-3 seconds per page at 150 DPI).

**Optimization options**:
- Parallel OCR (ThreadPoolExecutor)
- Lower DPI for separator detection (100 DPI is enough)
- Cache OCR results

**LLM calls**: ~1-2 seconds per document. Not parallelizable due to Ollama model concurrency limits.

### Known Limitations

1. **No scanner integration**: Uses scanline (separate tool). This is intentional — scanner drivers are platform-specific and messy.
2. **Local LLM only**: Requires Ollama. Could add cloud provider support (OpenAI, Anthropic) if needed.
3. **PDF only**: Doesn't handle images, Word docs, etc. Could add format conversion if needed.
4. **Single inbox**: Doesn't support multiple inbox folders. Easy to add if needed.

### Deployment

**Development:**
```bash
poetry install
poetry run docsplit watch
```

**Production:**
```bash
poetry build
pip install dist/docsplit-0.1.0-py3-none-any.whl
docsplit watch
```

Or run as systemd service / launchd daemon for always-on processing.

### Dependencies

Required system packages:
- **Tesseract**: `brew install tesseract` (macOS)
- **Poppler**: `brew install poppler` (for pdf2image)
- **Ollama**: `brew install ollama` + `ollama pull mistral`

Python packages managed by Poetry (see `pyproject.toml`).

### Code Quality

- **Type hints**: Full coverage (Python 3.12+)
- **Linting**: Black (formatter), Ruff (linter)
- **Tests**: pytest with coverage reporting
- **Documentation**: Docstrings on all public functions

### Migration from docproc

If you have an existing docproc setup:

1. Copy `config.example.yaml` to `~/.config/docsplit/config.yaml`
2. Update paths to match your current setup
3. Run `docsplit watch` in parallel with docproc for a trial period
4. Once confident, shut down docproc and use docsplit exclusively

Database is new — historical documents won't be in the DB unless you re-process them. That's fine; the filesystem is still the source of truth.
