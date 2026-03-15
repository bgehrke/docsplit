# TODO - Future Development

## Phase 3: Performance & Optimization

### High Priority
- [ ] **Parallel OCR processing** — Use ThreadPoolExecutor to OCR multiple pages simultaneously
- [ ] **OCR result caching** — Cache OCR results to avoid re-processing on retries
- [ ] **Optimize separator detection** — Use lower DPI (100) for separator pages, higher (200) for content
- [ ] **Batch LLM calls** — Send multiple documents to LLM in one request if supported
- [ ] **Memory optimization** — Stream large PDFs instead of loading all pages into memory

### Medium Priority
- [ ] **Watch mode improvements**
  - [ ] Parallel processing of multiple PDFs in inbox
  - [ ] Rate limiting for LLM calls
  - [ ] Graceful degradation when LLM is unavailable
- [ ] **Better error recovery**
  - [ ] Auto-retry failed documents from quarantine
  - [ ] Configurable retry intervals
  - [ ] Email/webhook notifications for failures

### Low Priority
- [ ] **Metrics and monitoring**
  - [ ] Processing time per document
  - [ ] OCR accuracy estimates
  - [ ] LLM confidence trends
  - [ ] Success/failure rates over time

---

## Features & Enhancements

### Document Processing
- [ ] **Multi-language OCR support** — Allow language selection per batch
- [ ] **QR code separator detection** — Alternative to text-based separators
- [ ] **Barcode support** — Extract data from barcodes on documents
- [ ] **Handwriting recognition** — Better OCR for handwritten notes
- [ ] **Form field extraction** — Extract specific fields from structured forms
- [ ] **Duplicate detection** — Flag/skip documents that have already been processed

### Archive Management
- [ ] **Document versioning** — Track changes to archived documents
- [ ] **Tagging system** — Add custom tags to documents
- [ ] **Full-text search** — Index OCR text for search (Elasticsearch or similar)
- [ ] **Document linking** — Link related documents together
- [ ] **Bulk operations** — Rename, move, or delete multiple documents
- [ ] **Export capabilities**
  - [ ] PDF export with annotations
  - [ ] CSV export of metadata
  - [ ] Backup/restore functionality

### Web UI
- [ ] **Mobile-responsive design** — Better mobile experience
- [ ] **Document preview** — View PDFs in browser
- [ ] **Edit metadata** — Manually correct LLM extractions
- [ ] **Bulk tagging interface** — Tag multiple documents at once
- [ ] **Advanced search filters**
  - [ ] Date ranges
  - [ ] Confidence thresholds
  - [ ] Multiple vendors
- [ ] **Dashboard** — Stats, charts, recent activity
- [ ] **User authentication** — Multi-user support with permissions

### Integration & Automation
- [ ] **Email ingestion** — Forward scans to an email address for processing
- [ ] **Cloud storage backends**
  - [ ] S3 support
  - [ ] Google Drive support
  - [ ] Dropbox support
- [ ] **Webhook triggers** — Send events to external systems
- [ ] **API endpoints** — RESTful API for external integrations
- [ ] **IFTTT/Zapier integration** — Connect to automation platforms
- [ ] **Calendar integration** — Add document dates to calendar

### Detection Engineering
- [ ] **Detection Studio** (deferred from Phase 1)
  - [ ] Sigma rule editor
  - [ ] ATT&CK coverage heatmap
  - [ ] Rule testing sandbox
  - [ ] CI/CD for detection deployment
- [ ] **Custom document type definitions** — User-defined document types beyond built-in list
- [ ] **Template matching** — Define document templates for better classification

---

## Code Quality & Testing

### Testing
- [ ] **Increase test coverage to 80%+**
- [ ] **Integration tests with sample PDFs**
- [ ] **End-to-end workflow tests**
- [ ] **LLM mock fixtures** — Deterministic tests without live LLM
- [ ] **Performance benchmarks** — Track processing speed over time
- [ ] **Regression test suite** — Prevent bugs from reappearing

### Documentation
- [ ] **API documentation** — Auto-generate from docstrings
- [ ] **Architecture diagrams** — Visual system overview
- [ ] **User guide** — Step-by-step tutorials
- [ ] **Video tutorials** — Screencasts for common workflows
- [ ] **Troubleshooting guide** — Common issues and solutions
- [ ] **Contributing guide** — How to contribute to the project

### Code Improvements
- [ ] **Type hint coverage** — 100% mypy strict compliance
- [ ] **Logging improvements** — Structured logging (JSON format)
- [ ] **Configuration validation** — Better error messages for invalid config
- [ ] **Plugin system** — Allow custom processors/enrichers
- [ ] **Internationalization (i18n)** — Multi-language UI support

---

## Deployment & Operations

### Packaging
- [ ] **Docker image** — Official Docker image with all dependencies
- [ ] **Kubernetes manifests** — Helm charts for K8s deployment
- [ ] **Homebrew formula** — Easy install on macOS
- [ ] **Snap package** — Easy install on Linux
- [ ] **Windows installer** — MSI or Chocolatey package

### Service Management
- [ ] **Systemd service** — Auto-start on Linux
- [ ] **launchd plist** — Auto-start on macOS
- [ ] **Health check endpoint** — `/health` for monitoring
- [ ] **Graceful shutdown** — Finish processing before exit
- [ ] **Log rotation** — Automatic log management
- [ ] **Update mechanism** — Check for new versions

### Security
- [ ] **Secrets management** — Vault integration for sensitive config
- [ ] **Audit logging** — Track all document access/modifications
- [ ] **Encryption at rest** — Encrypt archived documents
- [ ] **RBAC (Role-Based Access Control)** — Fine-grained permissions
- [ ] **SSO/SAML support** — Enterprise authentication
- [ ] **Security scanning** — Automated dependency vulnerability checks

---

## Known Issues & Bugs

### High Priority
- [ ] **Fix W2 vs W-2 inconsistency** — ✅ FIXED (v0.2.0)
- [ ] **Blank separator pages** — ✅ FIXED (v0.2.0)
- [ ] **Tax naming not applied with --dest** — ✅ FIXED (v0.2.0)

### Medium Priority
- [ ] **OCR accuracy on low-quality scans** — Needs preprocessing improvements
- [ ] **Date extraction failures** — LLM sometimes can't find dates
- [ ] **Vendor name variations** — Same company recognized as different vendors
- [ ] **Document type misclassification** — W-2 sometimes classified as "Other"

### Low Priority
- [ ] **Large PDF memory usage** — Need streaming for 100+ page files
- [ ] **Filename collision handling** — Current _001 suffix could be smarter
- [ ] **Web UI mobile keyboard** — Virtual keyboard covers search box

---

## Research & Exploration

### AI/ML Enhancements
- [ ] **Fine-tune LLM on tax documents** — Better tax form recognition
- [ ] **Custom OCR model** — Train on specific document types
- [ ] **Anomaly detection** — Detect unusual documents automatically
- [ ] **Auto-categorization** — Learn categories from user corrections
- [ ] **Document similarity** — Find similar documents using embeddings

### Advanced Features
- [ ] **Multi-modal processing** — Images, audio, video
- [ ] **Receipt parsing** — Extract line items from receipts
- [ ] **Invoice reconciliation** — Match invoices to payments
- [ ] **Compliance checking** — Flag documents missing required fields
- [ ] **Retention policies** — Auto-archive/delete based on age

### Alternative Technologies
- [ ] **GraphQL API** — Alternative to REST
- [ ] **Event sourcing** — Full audit trail with replay capability
- [ ] **CQRS pattern** — Separate read/write models
- [ ] **gRPC for internal services** — Faster inter-service communication

---

## Open Source Community

### Community Building
- [ ] **Contributing guidelines** — CONTRIBUTING.md
- [ ] **Code of conduct** — CODE_OF_CONDUCT.md
- [ ] **Issue templates** — Bug report, feature request templates
- [ ] **PR templates** — Standardize pull request format
- [ ] **Roadmap** — Public roadmap for transparency
- [ ] **Discussion forum** — GitHub Discussions or Discord

### Project Management
- [ ] **Milestone planning** — Define clear release milestones
- [ ] **Semantic versioning** — Proper version numbering
- [ ] **Changelog automation** — Auto-generate from commits
- [ ] **Release notes** — User-friendly release descriptions

---

## Version-Specific TODOs

### v0.3.0 (Next Release)
- [ ] Parallel OCR processing
- [ ] OCR caching
- [ ] Test coverage to 80%
- [ ] Mobile-responsive web UI

### v0.4.0
- [ ] Email ingestion
- [ ] Cloud storage backends (S3)
- [ ] Document preview in web UI
- [ ] User authentication

### v1.0.0 (Stable Release)
- [ ] 90%+ test coverage
- [ ] Full documentation
- [ ] Docker image
- [ ] Production-ready deployment guides
- [ ] Security audit
- [ ] Performance benchmarks

---

## Notes

**Priority Legend:**
- High: Critical for usability or blocking issues
- Medium: Important improvements, nice to have
- Low: Polish, optimization, edge cases

**Versioning Strategy:**
- Patch (0.2.x): Bug fixes only
- Minor (0.x.0): New features, backwards compatible
- Major (x.0.0): Breaking changes, major rewrites

**Decision Making:**
- User feedback drives feature priority
- Security and stability over new features
- Open source contributions welcome
- Maintain simplicity — don't over-engineer
