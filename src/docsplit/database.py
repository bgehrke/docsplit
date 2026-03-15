"""SQLite database for tracking processed documents."""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from .models import Batch, Document, ProcessingStatus

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    total_docs INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER,
    source_path TEXT NOT NULL,
    source_page_range TEXT,
    archive_path TEXT,
    vendor TEXT,
    doc_date TEXT,
    doc_type TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    confidence_score REAL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (batch_id) REFERENCES batches(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_batch ON documents(batch_id);
CREATE INDEX IF NOT EXISTS idx_documents_vendor ON documents(vendor);
CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(doc_date);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
"""


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: Path):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._conn() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_batch(self, batch: Batch) -> int:
        """
        Create a new batch record.

        Args:
            batch: Batch to insert

        Returns:
            Batch ID
        """
        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO batches (source_path, processed_at, total_docs, success_count, error_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(batch.source_path),
                    batch.processed_at.isoformat(),
                    batch.total_docs,
                    batch.success_count,
                    batch.error_count,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def update_batch_counts(self, batch_id: int, total: int, success: int, errors: int) -> None:
        """
        Update batch document counts.

        Args:
            batch_id: Batch ID
            total: Total documents
            success: Successful documents
            errors: Failed documents
        """
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE batches
                SET total_docs = ?, success_count = ?, error_count = ?
                WHERE id = ?
                """,
                (total, success, errors, batch_id),
            )
            conn.commit()

    def create_document(self, doc: Document) -> int:
        """
        Create a new document record.

        Args:
            doc: Document to insert

        Returns:
            Document ID
        """
        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO documents (
                    batch_id, source_path, source_page_range, archive_path,
                    vendor, doc_date, doc_type, status, error_message,
                    confidence_score, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.batch_id,
                    str(doc.source_path),
                    doc.source_page_range,
                    str(doc.archive_path) if doc.archive_path else None,
                    doc.metadata.vendor,
                    doc.metadata.date,
                    doc.metadata.document_type.value,
                    doc.status.value,
                    doc.error_message,
                    doc.confidence_score,
                    doc.created_at.isoformat(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def update_document_status(
        self,
        doc_id: int,
        status: ProcessingStatus,
        archive_path: Optional[Path] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update document processing status.

        Args:
            doc_id: Document ID
            status: New status
            archive_path: Archive path (if successful)
            error_message: Error message (if failed)
        """
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE documents
                SET status = ?, archive_path = ?, error_message = ?
                WHERE id = ?
                """,
                (status.value, str(archive_path) if archive_path else None, error_message, doc_id),
            )
            conn.commit()

    def search_documents(
        self,
        vendor: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        doc_type: Optional[str] = None,
        status: Optional[ProcessingStatus] = None,
        limit: int = 100,
    ) -> list[sqlite3.Row]:
        """
        Search documents.

        Args:
            vendor: Filter by vendor (partial match)
            year: Filter by year
            month: Filter by month
            doc_type: Filter by document type
            status: Filter by status
            limit: Maximum results

        Returns:
            List of document records
        """
        query = "SELECT * FROM documents WHERE 1=1"
        params = []

        if vendor:
            query += " AND vendor LIKE ?"
            params.append(f"%{vendor}%")

        if year:
            query += " AND doc_date LIKE ?"
            params.append(f"{year}-%")

        if month:
            query += " AND doc_date LIKE ?"
            params.append(f"{year}-{month:02d}%")

        if doc_type:
            query += " AND doc_type = ?"
            params.append(doc_type)

        if status:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def get_batch_summary(self, batch_id: int) -> Optional[sqlite3.Row]:
        """Get batch summary with stats."""
        with self._conn() as conn:
            cursor = conn.execute("SELECT * FROM batches WHERE id = ?", (batch_id,))
            return cursor.fetchone()

    def get_recent_batches(self, limit: int = 10) -> list[sqlite3.Row]:
        """Get recent batches."""
        with self._conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM batches ORDER BY processed_at DESC LIMIT ?", (limit,)
            )
            return cursor.fetchall()
