"""Simple web UI for document search and review."""

import logging
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

from .config import Config, load_config
from .database import Database
from .models import ProcessingStatus

logger = logging.getLogger(__name__)

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>docsplit - Document Archive</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
        }
        .search-box {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .search-box input, .search-box select {
            padding: 8px 12px;
            margin-right: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .search-box button {
            padding: 8px 16px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .search-box button:hover {
            background: #0056b3;
        }
        .results {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .document {
            border-bottom: 1px solid #eee;
            padding: 15px 0;
        }
        .document:last-child {
            border-bottom: none;
        }
        .document-path {
            font-weight: 600;
            color: #007bff;
            margin-bottom: 5px;
        }
        .document-meta {
            color: #666;
            font-size: 14px;
        }
        .status {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-success {
            background: #d4edda;
            color: #155724;
        }
        .status-failed {
            background: #f8d7da;
            color: #721c24;
        }
        .confidence {
            color: #888;
            font-size: 12px;
        }
        .no-results {
            text-align: center;
            color: #999;
            padding: 40px;
        }
    </style>
</head>
<body>
    <h1>📄 docsplit Archive</h1>

    <div class="search-box">
        <h3>Search Documents</h3>
        <form id="searchForm">
            <input type="text" id="vendor" name="vendor" placeholder="Vendor name">
            <input type="number" id="year" name="year" placeholder="Year">
            <input type="number" id="month" name="month" placeholder="Month">
            <select id="status" name="status">
                <option value="">All statuses</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
            </select>
            <button type="submit">Search</button>
        </form>
    </div>

    <div class="results" id="results">
        <p class="no-results">Enter search criteria and click Search</p>
    </div>

    <script>
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const params = new URLSearchParams();
            const vendor = document.getElementById('vendor').value;
            const year = document.getElementById('year').value;
            const month = document.getElementById('month').value;
            const status = document.getElementById('status').value;

            if (vendor) params.append('vendor', vendor);
            if (year) params.append('year', year);
            if (month) params.append('month', month);
            if (status) params.append('status', status);

            const response = await fetch('/api/search?' + params);
            const data = await response.json();

            const resultsDiv = document.getElementById('results');

            if (data.documents.length === 0) {
                resultsDiv.innerHTML = '<p class="no-results">No documents found</p>';
                return;
            }

            let html = '<h3>Found ' + data.documents.length + ' document(s)</h3>';

            data.documents.forEach(doc => {
                const statusClass = 'status-' + doc.status;
                const confidence = doc.confidence_score !== null
                    ? (doc.confidence_score * 100).toFixed(0) + '%'
                    : 'N/A';

                html += `
                    <div class="document">
                        <div class="document-path">${doc.archive_path || 'N/A'}</div>
                        <div class="document-meta">
                            <strong>Vendor:</strong> ${doc.vendor} &nbsp;|&nbsp;
                            <strong>Date:</strong> ${doc.doc_date || 'N/A'} &nbsp;|&nbsp;
                            <strong>Type:</strong> ${doc.doc_type} &nbsp;|&nbsp;
                            <span class="status ${statusClass}">${doc.status}</span> &nbsp;|&nbsp;
                            <span class="confidence">Confidence: ${confidence}</span>
                        </div>
                        ${doc.error_message ? '<div style="color: red; font-size: 12px;">Error: ' + doc.error_message + '</div>' : ''}
                    </div>
                `;
            });

            resultsDiv.innerHTML = html;
        });
    </script>
</body>
</html>
"""


def create_app(config: Config, db: Database) -> Flask:
    """Create Flask application."""
    app = Flask(__name__)

    @app.route("/")
    def index():
        """Render main page."""
        return render_template_string(HTML_TEMPLATE)

    @app.route("/api/search")
    def api_search():
        """Search documents API endpoint."""
        vendor = request.args.get("vendor")
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        status_str = request.args.get("status")

        status = None
        if status_str:
            status = ProcessingStatus(status_str)

        results = db.search_documents(
            vendor=vendor, year=year, month=month, status=status, limit=100
        )

        documents = []
        for row in results:
            documents.append(
                {
                    "id": row["id"],
                    "vendor": row["vendor"],
                    "doc_date": row["doc_date"],
                    "doc_type": row["doc_type"],
                    "archive_path": row["archive_path"],
                    "status": row["status"],
                    "confidence_score": row["confidence_score"],
                    "error_message": row["error_message"],
                }
            )

        return jsonify({"documents": documents, "total": len(documents)})

    @app.route("/api/stats")
    def api_stats():
        """Get overall statistics."""
        recent_batches = db.get_recent_batches(limit=10)

        batches = []
        for row in recent_batches:
            batches.append(
                {
                    "id": row["id"],
                    "source_path": row["source_path"],
                    "processed_at": row["processed_at"],
                    "total_docs": row["total_docs"],
                    "success_count": row["success_count"],
                    "error_count": row["error_count"],
                }
            )

        return jsonify({"recent_batches": batches})

    return app


def start_web_ui(config: Config, db: Database, host: str = "127.0.0.1", port: int = 5000):
    """Start web UI server."""
    app = create_app(config, db)
    logger.info(f"Starting web UI at http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
