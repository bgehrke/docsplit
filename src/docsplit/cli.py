"""Command-line interface for docsplit."""

import argparse
import logging
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from . import __version__
from .archive import archive_document
from .config import Config, load_config
from .database import Database
from .metadata import extract_metadata
from .models import Batch, Document, ProcessingStatus
from .scanner import split_pdf_on_separators
from .separator import create_separator_sheet
from .watcher import InboxWatcher
from .web import start_web_ui

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def process_batch(
    pdf_path: Path,
    config: Config,
    db: Database,
    dry_run: bool = False,
    dest_override: str | None = None,
) -> None:
    """
    Process a batch-scanned PDF.

    Args:
        pdf_path: Path to batch PDF
        config: Application configuration
        db: Database instance
        dry_run: If True, don't make changes
        dest_override: Manual destination path override
    """
    # Create batch record
    batch = Batch(source_path=pdf_path, processed_at=datetime.now())
    batch_id = None if dry_run else db.create_batch(batch)

    results = []

    # Create temp directory for split documents
    with tempfile.TemporaryDirectory(prefix="docsplit_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Split on separators
        logger.info(f"Processing: {pdf_path.name}")
        split_docs = split_pdf_on_separators(pdf_path, temp_dir, config)

        # Process each document
        for i, doc_path in enumerate(split_docs, 1):
            logger.info(f"\nDocument {i}/{len(split_docs)}: {doc_path.name}")

            try:
                # Extract metadata
                metadata, confidence = extract_metadata(doc_path, config)

                # Create document record
                doc = Document(
                    batch_id=batch_id,
                    source_path=doc_path,
                    metadata=metadata,
                    confidence_score=confidence,
                    status=ProcessingStatus.PENDING,
                )

                # Archive the document
                if not dry_run:
                    archive_path = archive_document(
                        doc_path, metadata, config, dry_run=False, dest_override=dest_override
                    )
                    doc.archive_path = archive_path
                    doc.status = ProcessingStatus.SUCCESS

                    # Save to database
                    doc.id = db.create_document(doc)
                else:
                    logger.info(f"[DRY RUN] Would archive with metadata: {metadata}")
                    if dest_override:
                        logger.info(f"[DRY RUN] Destination override: {dest_override}")

                results.append(doc)

            except Exception as e:
                logger.error(f"Failed to process document: {e}", exc_info=True)

                doc = Document(
                    batch_id=batch_id,
                    source_path=doc_path,
                    metadata=metadata if "metadata" in locals() else None,
                    status=ProcessingStatus.FAILED,
                    error_message=str(e),
                )

                if not dry_run:
                    db.create_document(doc)

                results.append(doc)

    # Update batch counts
    if not dry_run and batch_id:
        success = sum(1 for d in results if d.status == ProcessingStatus.SUCCESS)
        failed = sum(1 for d in results if d.status == ProcessingStatus.FAILED)
        db.update_batch_counts(batch_id, len(results), success, failed)

    # Print summary
    print_summary(results, dry_run)


def print_summary(documents: list[Document], dry_run: bool = False) -> None:
    """Print processing summary."""
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)

    successful = [d for d in documents if d.status == ProcessingStatus.SUCCESS]
    failed = [d for d in documents if d.status == ProcessingStatus.FAILED]

    print(f"Total documents: {len(documents)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print("\nProcessed documents:")
        for doc in successful:
            print(f"  {doc.archive_path.name if doc.archive_path else 'N/A'}")
            print(f"    Vendor: {doc.metadata.vendor}")
            print(f"    Date: {doc.metadata.date or 'N/A'}")
            print(f"    Type: {doc.metadata.document_type.value}")

    if failed:
        print("\nFailed documents:")
        for doc in failed:
            print(f"  {doc.source_path.name}: {doc.error_message}")

    print("=" * 60)


def cmd_process(args: argparse.Namespace, config: Config, db: Database) -> None:
    """Process command handler."""
    pdf_path = Path(args.input).expanduser()

    if not pdf_path.exists():
        logger.error(f"File not found: {pdf_path}")
        sys.exit(1)

    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        logger.error(f"Input must be a PDF file: {pdf_path}")
        sys.exit(1)

    dest_override = getattr(args, "dest", None)
    process_batch(pdf_path, config, db, dry_run=args.dry_run, dest_override=dest_override)


def cmd_watch(args: argparse.Namespace, config: Config, db: Database) -> None:
    """Watch command handler."""

    def process_callback(pdf_path: Path) -> None:
        """Callback for processing PDFs in watch mode."""
        process_batch(pdf_path, config, db, dry_run=args.dry_run)

    watcher = InboxWatcher(config, process_callback)
    watcher.watch()


def cmd_separator(args: argparse.Namespace, config: Config, db: Database) -> None:
    """Separator command handler."""
    output_path = Path(args.output).expanduser() if args.output else Path("separator.pdf")
    create_separator_sheet(output_path, config.separator.text)
    print(f"\nSeparator sheet created: {output_path}")
    print("Print this page and use it to separate documents when batch scanning.")


def cmd_search(args: argparse.Namespace, config: Config, db: Database) -> None:
    """Search command handler."""
    results = db.search_documents(
        vendor=args.vendor,
        year=args.year,
        month=args.month,
        doc_type=args.type,
        limit=args.limit,
    )

    if not results:
        print("No documents found.")
        return

    print(f"\nFound {len(results)} document(s):\n")
    for row in results:
        print(f"  {row['archive_path']}")
        print(f"    Vendor: {row['vendor']}")
        print(f"    Date: {row['doc_date']}")
        print(f"    Type: {row['doc_type']}")
        print(f"    Status: {row['status']}")
        if row['confidence_score']:
            print(f"    Confidence: {row['confidence_score']:.0%}")
        print()


def cmd_web(args: argparse.Namespace, config: Config, db: Database) -> None:
    """Web UI command handler."""
    print(f"Starting web UI at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop\n")
    start_web_ui(config, db, host=args.host, port=args.port)


def cmd_reprocess(args: argparse.Namespace, config: Config, db: Database) -> None:
    """Reprocess command handler."""
    # Find failed documents or specific batch
    if args.batch_id:
        # Reprocess a specific batch
        batch_summary = db.get_batch_summary(args.batch_id)
        if not batch_summary:
            logger.error(f"Batch {args.batch_id} not found")
            sys.exit(1)

        source_path = Path(batch_summary["source_path"])
        if not source_path.exists():
            logger.error(f"Source file not found: {source_path}")
            logger.info("Check the Processed folder for the original file")
            sys.exit(1)

        logger.info(f"Reprocessing batch {args.batch_id}: {source_path.name}")
        process_batch(source_path, config, db, dry_run=args.dry_run)

    elif args.failed:
        # Reprocess all failed documents
        failed_docs = db.search_documents(status=ProcessingStatus.FAILED, limit=1000)

        if not failed_docs:
            print("No failed documents found.")
            return

        print(f"Found {len(failed_docs)} failed document(s)")

        # Group by batch
        batch_ids = set(row["batch_id"] for row in failed_docs if row["batch_id"])

        for batch_id in batch_ids:
            batch_summary = db.get_batch_summary(batch_id)
            if batch_summary:
                source_path = Path(batch_summary["source_path"])
                if source_path.exists():
                    logger.info(f"\nReprocessing batch {batch_id}: {source_path.name}")
                    process_batch(source_path, config, db, dry_run=args.dry_run)
                else:
                    logger.warning(f"Source not found for batch {batch_id}: {source_path}")

    else:
        logger.error("Must specify --batch-id or --failed")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated document splitting and archival",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Don't make changes")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Process command
    process_parser = subparsers.add_parser("process", help="Process a single PDF file")
    process_parser.add_argument("input", type=str, help="PDF file to process")
    process_parser.add_argument(
        "--dest",
        type=str,
        help='Archive destination override (e.g., "2025/tax-documents" or "{year}/receipts")',
    )

    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Monitor inbox folder")

    # Separator command
    sep_parser = subparsers.add_parser("separator", help="Generate separator sheet")
    sep_parser.add_argument("-o", "--output", type=str, help="Output path (default: separator.pdf)")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search archived documents")
    search_parser.add_argument("--vendor", type=str, help="Filter by vendor")
    search_parser.add_argument("--year", type=int, help="Filter by year")
    search_parser.add_argument("--month", type=int, help="Filter by month")
    search_parser.add_argument("--type", type=str, help="Filter by document type")
    search_parser.add_argument("--limit", type=int, default=100, help="Max results (default: 100)")

    # Web UI command
    web_parser = subparsers.add_parser("web", help="Start web UI")
    web_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    web_parser.add_argument("--port", type=int, default=5000, help="Port to bind to")

    # Reprocess command
    reprocess_parser = subparsers.add_parser("reprocess", help="Reprocess documents")
    reprocess_parser.add_argument("--batch-id", type=int, help="Reprocess specific batch")
    reprocess_parser.add_argument("--failed", action="store_true", help="Reprocess all failed documents")

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load config
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.info("Create a config file at ~/.config/docsplit/config.yaml")
        logger.info("See config.example.yaml for template")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Initialize database
    db = Database(config.paths.database)

    # Route to command handlers
    if args.command == "process":
        cmd_process(args, config, db)
    elif args.command == "watch":
        cmd_watch(args, config, db)
    elif args.command == "separator":
        cmd_separator(args, config, db)
    elif args.command == "search":
        cmd_search(args, config, db)
    elif args.command == "web":
        cmd_web(args, config, db)
    elif args.command == "reprocess":
        cmd_reprocess(args, config, db)


if __name__ == "__main__":
    main()
