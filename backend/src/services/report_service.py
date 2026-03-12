from __future__ import annotations

import datetime as dt
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from src.services.trace_service import run_trace


def strip_simple_tags(html_text: str) -> str:
    text = re.sub(r"<[^>]+>", "", html_text)
    return html.unescape(text).strip()


def split_caption_and_table(block_html: str) -> tuple[str, str]:
    caption_match = re.search(r"<div class='table-caption'>(.*?)</div>", block_html, flags=re.DOTALL)
    table_match = re.search(r"(<table.*</table>)", block_html, flags=re.DOTALL)
    caption = strip_simple_tags(caption_match.group(1)) if caption_match else ""
    table_html = table_match.group(1) if table_match else block_html
    return caption, table_html


def render_block_markdown(block: dict[str, str]) -> list[str]:
    block_type = block.get("type", "")
    block_html = block.get("html", "")
    if block_type == "text":
        return [strip_simple_tags(block_html), ""]
    if block_type == "table":
        caption, table_html = split_caption_and_table(block_html)
        lines = []
        if caption:
            lines.append(f"**{caption}**")
            lines.append("")
        lines.append(table_html)
        lines.append("")
        return lines
    return [block_html, ""]


def render_node_markdown(node: dict[str, Any], level: int) -> list[str]:
    title = node.get("title", "Шаг")
    lines = [f"{'#' * level} {title}", ""]
    for block in node.get("blocks", []):
        lines.extend(render_block_markdown(block))
    for child in node.get("steps", []):
        lines.extend(render_node_markdown(child, level + 1))
    return lines


def build_markdown_report(result: dict[str, Any], payload: dict[str, Any]) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Полный отчет по решению",
        "",
        f"- Дата: {now}",
        "",
        "## Входные данные",
        "",
        "```json",
        json.dumps(payload, ensure_ascii=False, indent=2),
        "```",
        "",
    ]

    for idx, action in enumerate(result.get("actions", []), start=1):
        action_copy = dict(action)
        action_copy["title"] = f"{idx}. {action.get('title', 'Действие')}"
        lines.extend(render_node_markdown(action_copy, 2))

    return "\n".join(lines).strip() + "\n"


def markdown_to_pdf_bytes(markdown: str) -> bytes:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        md_path = tmp_path / "report.md"
        pdf_path = tmp_path / "report.pdf"
        css_path = tmp_path / "report.css"
        md_path.write_text(markdown, encoding="utf-8")
        css_path.write_text(
            """
@page {
  size: A4;
  margin: 1cm;
}

body {
  font-size: 10pt;
  line-height: 1.15;
}

h1 {
  font-size: 13pt;
  margin: 0 0 8px 0;
}

h2 {
  font-size: 12pt;
  margin: 8px 0 6px 0;
}

h3, h4, h5, h6 {
  font-size: 11pt;
  margin: 6px 0 4px 0;
}

p, li {
  font-size: 10pt;
  margin: 3px 0;
}

table {
  width: auto;
  max-width: 100%;
  border-collapse: collapse;
  table-layout: auto;
  font-size: 9pt;
}

th, td {
  border: 1px solid #777;
  padding: 2px 3px;
  word-wrap: break-word;
  text-align: left;
  vertical-align: top;
}

th {
  text-align: left !important;
}
            """.strip(),
            encoding="utf-8",
        )

        command = [
            "pandoc",
            str(md_path),
            "-o",
            str(pdf_path),
            "--from",
            "gfm+raw_html",
            "--pdf-engine",
            "weasyprint",
            "--css",
            str(css_path),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError("pandoc не найден на сервере. Установите pandoc для экспорта PDF.") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else str(exc)
            raise RuntimeError(f"Не удалось собрать PDF через pandoc: {stderr}") from exc

        return pdf_path.read_bytes()


def build_pdf_report(payload: dict[str, Any]) -> tuple[str, str, bytes]:
    result = run_trace(payload)
    markdown = build_markdown_report(result, payload)
    pdf_bytes = markdown_to_pdf_bytes(markdown)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"gost-full-report-{timestamp}.pdf"
    return filename, markdown, pdf_bytes
