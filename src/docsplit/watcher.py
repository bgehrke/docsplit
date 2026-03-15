"""Watch folder for new PDFs and process them."""

import logging
import shutil
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from .config import Config

logger = logging.getLogger(__name__)


def is_file_stable(filepath: Path, wait_seconds: float = 1.0) -> bool:
    """
    Check if file size is stable (not being written).

    Args:
        filepath: Path to file
        wait_seconds: How long to wait between size checks

    Returns:
        True if file size is stable
    """
    try:
        size1 = filepath.stat().st_size
        time.sleep(wait_seconds)
        size2 = filepath.stat().st_size
        return size1 == size2
    except FileNotFoundError:
        return False


class InboxWatcher:
    """Monitor inbox folder and process new PDFs."""

    def __init__(self, config: Config, process_callback: Callable[[Path], None]):
        """
        Initialize watcher.

        Args:
            config: Application configuration
            process_callback: Function to call for each new PDF
        """
        self.config = config
        self.process_callback = process_callback
        self.running = False
        self.processing: set[str] = set()

    def _setup_signal_handlers(self) -> None:
        """Set up graceful shutdown signal handlers."""

        def signal_handler(signum: int, frame: object) -> None:
            logger.info("Shutdown signal received...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def watch(self) -> None:
        """
        Start watching inbox folder.

        Runs until interrupted (Ctrl+C).
        """
        inbox_dir = self.config.paths.inbox
        inbox_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Watching for files in: {inbox_dir}")
        logger.info(f"Check interval: {self.config.watch.interval} seconds")
        logger.info("Press Ctrl+C to stop\n")

        self._setup_signal_handlers()
        self.running = True

        while self.running:
            try:
                self._check_inbox()
                time.sleep(self.config.watch.interval)
            except Exception as e:
                logger.error(f"Error in watch loop: {e}", exc_info=True)
                time.sleep(self.config.watch.interval)

        logger.info("Stopped watching.")

    def _check_inbox(self) -> None:
        """Check inbox for new PDFs and process them."""
        inbox_dir = self.config.paths.inbox
        pdf_files = list(inbox_dir.glob("*.pdf"))

        for pdf_file in pdf_files:
            # Skip if already processing
            if pdf_file.name in self.processing:
                continue

            # Check file stability if enabled
            if self.config.watch.stability_check:
                if not is_file_stable(pdf_file):
                    logger.debug(f"Skipping {pdf_file.name} - still being written")
                    continue

            # Mark as processing
            self.processing.add(pdf_file.name)

            logger.info(f"\n{'=' * 60}")
            logger.info(f"New file detected: {pdf_file.name}")
            logger.info("=" * 60)

            try:
                # Process the file
                self.process_callback(pdf_file)

                # Move to processed folder
                processed_dir = self.config.paths.processed
                processed_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_name = f"{timestamp}_{pdf_file.name}"
                dest_path = processed_dir / dest_name

                shutil.move(str(pdf_file), str(dest_path))
                logger.info(f"Original moved to: {dest_path}")

            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}", exc_info=True)

                # Move to quarantine
                try:
                    quarantine_dir = self.config.paths.quarantine
                    quarantine_dir.mkdir(parents=True, exist_ok=True)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest_name = f"{timestamp}_{pdf_file.name}"
                    dest_path = quarantine_dir / dest_name

                    if pdf_file.exists():
                        shutil.move(str(pdf_file), str(dest_path))
                        logger.info(f"Moved to quarantine: {dest_path}")

                        # Write error log
                        error_log = dest_path.with_suffix(".error.txt")
                        error_log.write_text(f"{timestamp}\n{str(e)}\n")

                except Exception as e2:
                    logger.error(f"Failed to quarantine file: {e2}")

            finally:
                # Remove from processing set
                self.processing.discard(pdf_file.name)
