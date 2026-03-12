from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from src.services.report_service import build_markdown_report, markdown_to_pdf_bytes  # noqa: E402
from src.services.trace_service import run_trace  # noqa: E402


def read_payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload_json:
        payload_path = Path(args.payload_json).resolve()
        if not payload_path.exists():
            raise FileNotFoundError(f"Не найден файл payload: {payload_path}")
        return json.loads(payload_path.read_text(encoding="utf-8"))

    required = [args.source_bytes, args.a_mapping, args.b_mapping, args.key_bytes]
    if all(required):
        return {
            "sourceBytes": args.source_bytes,
            "aMapping": args.a_mapping,
            "bMapping": args.b_mapping,
            "keyBytes": args.key_bytes,
        }

    print("Введите данные для расчета отчета:")
    source = input("sourceBytes (16 hex): ").strip()
    a_mapping = input("aMapping (16 индексов): ").strip()
    b_mapping = input("bMapping (16 индексов): ").strip()
    key = input("keyBytes (16 hex): ").strip()
    return {"sourceBytes": source, "aMapping": a_mapping, "bMapping": b_mapping, "keyBytes": key}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Генерация полного отчета: сначала Markdown, потом (опционально) PDF."
    )
    parser.add_argument("--payload-json", help="Путь к JSON с полями sourceBytes/aMapping/bMapping/keyBytes")
    parser.add_argument("--source-bytes", help="16 hex-байтов source")
    parser.add_argument("--a-mapping", help="16 индексов для a")
    parser.add_argument("--b-mapping", help="16 индексов для b")
    parser.add_argument("--key-bytes", help="16 hex-байтов key")
    parser.add_argument("--output-dir", default=str(ROOT_DIR / "reports"), help="Каталог для отчетов")
    parser.add_argument("--name", help="Базовое имя файла отчета (без расширения)")
    parser.add_argument("--skip-pdf", action="store_true", help="Не пытаться создавать PDF")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = read_payload_from_args(args)
    result = run_trace(payload)
    markdown = build_markdown_report(result, payload)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base_name = args.name or f"gost-full-report-{timestamp}"
    md_path = output_dir / f"{base_name}.md"
    pdf_path = output_dir / f"{base_name}.pdf"

    md_path.write_text(markdown, encoding="utf-8")
    print(f"Markdown отчет создан: {md_path}")

    if args.skip_pdf:
        print("PDF пропущен (флаг --skip-pdf).")
        return

    try:
        pdf_bytes = markdown_to_pdf_bytes(markdown)
        pdf_path.write_bytes(pdf_bytes)
        print(f"PDF создан: {pdf_path}")
    except RuntimeError as exc:
        print(str(exc))
        print("Сохранился только .md файл. Это нормально, можно конвертировать позже.")


if __name__ == "__main__":
    main()
