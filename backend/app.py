from __future__ import annotations

import io
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

from src.services.report_service import build_pdf_report
from src.services.trace_service import run_trace


DIST_DIR = Path(__file__).resolve().parent / "dist"
app = Flask(__name__, static_folder=str(DIST_DIR), static_url_path="")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/run")
def run():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Тело запроса должно быть JSON."}), 400
    try:
        result = run_trace(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Внутренняя ошибка сервера: {exc}"}), 500
    return jsonify(result)


@app.post("/api/report/pdf")
def report_pdf():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Тело запроса должно быть JSON."}), 400
    try:
        filename, _, pdf_bytes = build_pdf_report(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": f"Внутренняя ошибка сервера: {exc}"}), 500

    download_name = filename or f"gost-full-report-{datetime.now():%Y%m%d-%H%M%S}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=download_name,
    )


@app.get("/")
def index():
    index_path = DIST_DIR / "index.html"
    if not index_path.exists():
        return (
            jsonify(
                {
                    "error": "Frontend не собран. Выполните: cd frontend && npm install && npm run build"
                }
            ),
            500,
        )
    return send_from_directory(DIST_DIR, "index.html")


@app.get("/<path:path>")
def spa(path: str):
    index_path = DIST_DIR / "index.html"
    if not index_path.exists():
        return (
            jsonify(
                {
                    "error": "Frontend не собран. Выполните: cd frontend && npm install && npm run build"
                }
            ),
            500,
        )
    target = DIST_DIR / path
    if target.exists() and target.is_file():
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, "index.html")


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
