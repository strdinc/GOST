from __future__ import annotations

import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from src.services.trace_service import run_trace  # noqa: E402


def ask(prompt: str) -> str:
    return input(f"{prompt}\n> ").strip()


def render_node(node: dict, path: str) -> str:
    title = node.get("title", "Шаг")
    blocks = node.get("blocks", [])
    steps = node.get("steps", [])

    blocks_html = "".join(block.get("html", "") for block in blocks)
    children_html = ""
    for idx, child in enumerate(steps, start=1):
        children_html += render_node(child, f"{path}.{idx}")

    return (
        "<details class='node'>"
        f"<summary><span class='badge'>{path}</span>{title}</summary>"
        f"<div class='body'>{blocks_html}{children_html}</div>"
        "</details>"
    )


def build_html_report(result: dict) -> str:
    actions = result.get("actions", [])
    summary_html = result.get("summaryTableHtml", "")
    rendered_actions = "".join(render_node(action, str(idx + 1)) for idx, action in enumerate(actions))

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Kuznyechik Trace Report</title>
  <style>
    body {{
      margin: 0;
      padding: 20px;
      color: #142033;
      background: #ecf4ff;
      font-family: "Segoe UI", Tahoma, sans-serif;
    }}
    .panel {{
      background: #fff;
      border: 1px solid #c9daed;
      border-radius: 12px;
      padding: 12px;
      margin-bottom: 12px;
    }}
    .node {{
      border: 1px solid #c9daed;
      border-radius: 10px;
      margin: 8px 0;
      background: #fbfdff;
    }}
    .node summary {{
      cursor: pointer;
      padding: 8px 10px;
      background: #eef5ff;
      list-style: none;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }}
    .node summary::-webkit-details-marker {{
      display: none;
    }}
    .badge {{
      min-width: 28px;
      border-radius: 999px;
      padding: 2px 8px;
      color: #fff;
      background: #2467db;
      font-size: 12px;
      text-align: center;
    }}
    .body {{
      padding: 10px;
    }}
    .table-caption {{
      margin: 8px 0 6px;
      color: #50617b;
      font-size: 13px;
    }}
    table.trace-table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 10px;
      font-size: 13px;
    }}
    table.trace-table th,
    table.trace-table td {{
      border: 1px solid #c9daed;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }}
    table.trace-table th {{
      background: #edf5ff;
    }}
  </style>
</head>
<body>
  <section class="panel">
    <h1>Отчет по преобразованиям Кузнечика</h1>
    <p>Этот файл сформирован из структурированных шагов без терминального вывода.</p>
  </section>
  <section class="panel">
    <h2>Финальная сводка</h2>
    {summary_html}
  </section>
  <section class="panel">
    <h2>Пошаговая трассировка</h2>
    {rendered_actions}
  </section>
</body>
</html>"""


def main() -> None:
    print("Введите исходные данные для генерации HTML-отчета.")
    source_bytes = ask("Исходные байты source (16 hex, через пробел)")
    a_mapping = ask("Индексы для a (16 чисел 0..15)")
    b_mapping = ask("Индексы для b (16 чисел 0..15)")
    key_bytes = ask("Ключ k (16 hex, через пробел)")

    payload = {
        "sourceBytes": source_bytes,
        "aMapping": a_mapping,
        "bMapping": b_mapping,
        "keyBytes": key_bytes,
    }

    result = run_trace(payload)
    report_html = build_html_report(result)

    report_path = ROOT / "trace_report.html"
    report_path.write_text(report_html, encoding="utf-8")
    (ROOT / "trace_payload.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Готово. Отчет сохранен: {report_path}")


if __name__ == "__main__":
    main()
