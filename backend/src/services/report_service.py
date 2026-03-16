from __future__ import annotations

import datetime as dt
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from src.services.trace_service import (
    L_COEFS,
    b8,
    bytes_bin_str,
    bytes_hex_str,
    gf_mul_fast,
    parse_hex_vector,
    parse_mapping,
    r_fast,
    r_inv_fast,
    run_trace,
    s_fast,
)


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

    checks_html = result.get("checksTableHtml", "")
    if checks_html:
        lines.extend(["## Финальная проверка", "", checks_html, ""])

    return "\n".join(lines).strip() + "\n"


def build_vector_by_mapping(source: list[int], mapping: list[int]) -> list[int]:
    return [source[index] for index in mapping]


def render_mapping_lines(source_name: str, target_name: str, mapping: list[int]) -> list[str]:
    lines = [f"## Построение вектора {target_name}", ""]
    for idx, source_index in enumerate(mapping):
        lines.append(f"- {target_name}{idx} = {source_name}{source_index}")
    lines.append("")
    return lines


def render_vector_lines(title: str, values: list[int]) -> list[str]:
    lines = [f"## {title}", "", f"{title}: {bytes_bin_str(values)}", ""]
    return lines


def render_xor_lines(title: str, left: list[int], right: list[int]) -> tuple[list[int], list[str]]:
    result = [left_value ^ right_value for left_value, right_value in zip(left, right)]
    lines = [f"## {title}", ""]
    for idx, (left_value, right_value, result_value) in enumerate(zip(left, right, result)):
        lines.append(f"- [{idx}] {b8(left_value)} XOR {b8(right_value)} = {b8(result_value)}")
    lines.append("")
    lines.append(f"Результат: {bytes_bin_str(result)}")
    lines.append("")
    return result, lines


def render_s_lines(title: str, source: list[int], inverse: bool = False) -> tuple[list[int], list[str]]:
    result = s_fast(source, inverse=inverse)
    lines = [f"## {title}", ""]
    for idx, (before, after) in enumerate(zip(source, result)):
        lines.append(f"- [{idx}] {b8(before)} -> {b8(after)}")
    lines.append("")
    lines.append(f"Результат: {bytes_bin_str(result)}")
    lines.append("")
    return result, lines


def render_l_function_lines(source: list[int], label: str) -> tuple[int, list[str]]:
    products: list[int] = []
    lines = [f"### Вычисление {label}", ""]
    for idx, (coef, value) in enumerate(zip(L_COEFS, source)):
        product = gf_mul_fast(coef, value)
        products.append(product)
        lines.append(f"- term {idx}: {b8(coef)} * {b8(value)} = {b8(product)}")

    lines.append("")
    lines.append("Последовательный XOR произведений:")
    accumulator = 0
    for idx, product in enumerate(products):
        before = accumulator
        accumulator ^= product
        lines.append(f"- step {idx}: {b8(before)} XOR {b8(product)} = {b8(accumulator)}")

    lines.append("")
    lines.append(f"{label} = {b8(accumulator)}")
    lines.append("")
    return accumulator, lines


def render_r_lines(source: list[int]) -> tuple[list[int], list[str]]:
    l_value, l_lines = render_l_function_lines(source, "l(a)")
    result = [l_value] + source[:15]
    lines = ["## R(a)", "", f"Вход: {bytes_bin_str(source)}", ""]
    lines.extend(l_lines)
    lines.append(f"R(a) = {bytes_bin_str(result)}")
    lines.append("")
    return result, lines


def render_r_inv_lines(source: list[int]) -> tuple[list[int], list[str]]:
    shifted = source[1:] + [source[0]]
    l_value, l_lines = render_l_function_lines(shifted, "l(shifted)")
    result = source[1:] + [l_value]
    lines = [
        "## R^-1(a)",
        "",
        f"Вход: {bytes_bin_str(source)}",
        "",
        f"shifted = {bytes_bin_str(shifted)}",
        "",
    ]
    lines.extend(l_lines)
    lines.append(f"R^-1(a) = {bytes_bin_str(result)}")
    lines.append("")
    return result, lines


def render_l_round_lines(title: str, source: list[int], inverse: bool = False) -> tuple[list[int], list[str]]:
    current = source[:]
    transform = r_inv_fast if inverse else r_fast
    lines = [f"## {title}", ""]
    for step in range(16):
        next_value = transform(current)
        lines.append(f"- Раунд {step + 1}: {bytes_bin_str(current)} -> {bytes_bin_str(next_value)}")
        current = next_value
    lines.append("")
    lines.append(f"Результат: {bytes_bin_str(current)}")
    lines.append("")
    return current, lines


def render_f_lines(key: list[int], a_vector: list[int], b_vector: list[int]) -> tuple[tuple[list[int], list[int]], list[str]]:
    x_result = [key_value ^ a_value for key_value, a_value in zip(key, a_vector)]
    s_result = s_fast(x_result)
    l_result = s_result[:]
    round_lines: list[str] = []
    for step in range(16):
        next_value = r_fast(l_result)
        round_lines.append(f"- Раунд L {step + 1}: {bytes_bin_str(l_result)} -> {bytes_bin_str(next_value)}")
        l_result = next_value
    first_result = [left ^ right for left, right in zip(l_result, b_vector)]
    second_result = a_vector[:]

    lines = ["## F[k](a, b)", ""]
    lines.append(f"Шаг X: {bytes_bin_str(key)} XOR {bytes_bin_str(a_vector)} = {bytes_bin_str(x_result)}")
    lines.append("")
    lines.append("Шаг S:")
    for idx, (before, after) in enumerate(zip(x_result, s_result)):
        lines.append(f"- [{idx}] {b8(before)} -> {b8(after)}")
    lines.append("")
    lines.append("Шаг L:")
    lines.extend(round_lines)
    lines.append("")
    lines.append(f"Шаг XOR с b: {bytes_bin_str(l_result)} XOR {bytes_bin_str(b_vector)} = {bytes_bin_str(first_result)}")
    lines.append(f"Второй выход: {bytes_bin_str(second_result)}")
    lines.append("")
    return (first_result, second_result), lines


def render_checks_lines(a_vector: list[int]) -> list[str]:
    s_ok = s_fast(s_fast(a_vector), inverse=True) == a_vector
    r_ok = r_inv_fast(r_fast(a_vector)) == a_vector
    l_ok = False
    l_forward = a_vector[:]
    for _ in range(16):
        l_forward = r_fast(l_forward)
    l_back = l_forward[:]
    for _ in range(16):
        l_back = r_inv_fast(l_back)
    l_ok = l_back == a_vector

    lines = [
        "## Проверки обратимости",
        "",
        f"- S^-1(S(a)) = a -> {'да' if s_ok else 'нет'}",
        f"- R^-1(R(a)) = a -> {'да' if r_ok else 'нет'}",
        f"- L^-1(L(a)) = a -> {'да' if l_ok else 'нет'}",
        "",
    ]
    return lines


def render_final_hex_lines(
    source: list[int],
    key: list[int],
    a_vector: list[int],
    b_vector: list[int],
    x_result: list[int],
    s_result: list[int],
    s_inv_result: list[int],
    r_result: list[int],
    r_inv_result: list[int],
    l_result: list[int],
    l_inv_result: list[int],
    f_result: tuple[list[int], list[int]],
) -> list[str]:
    first_result, second_result = f_result
    rows = [
        ("source", source),
        ("key", key),
        ("a", a_vector),
        ("b", b_vector),
        ("X[k](a)", x_result),
        ("S(a)", s_result),
        ("S^-1(a)", s_inv_result),
        ("R(a)", r_result),
        ("R^-1(a)", r_inv_result),
        ("L(a)", l_result),
        ("L^-1(a)", l_inv_result),
        ("F first", first_result),
        ("F second", second_result),
    ]
    lines = ["## Итоги в hex", ""]
    for title, values in rows:
        lines.append(f"- {title}: {bytes_hex_str(values)}")
    lines.append("")
    return lines


def build_simple_markdown_report(payload: dict[str, Any]) -> str:
    source = parse_hex_vector(payload.get("sourceBytes", ""), "sourceBytes")
    a_mapping = parse_mapping(payload.get("aMapping", ""), "aMapping")
    b_mapping = parse_mapping(payload.get("bMapping", ""), "bMapping")
    key = parse_hex_vector(payload.get("keyBytes", ""), "keyBytes")

    a_vector = build_vector_by_mapping(source, a_mapping)
    b_vector = build_vector_by_mapping(source, b_mapping)
    x_result, x_lines = render_xor_lines("X[k](a)", key, a_vector)
    s_result, s_lines = render_s_lines("S(a)", a_vector, inverse=False)
    s_inv_result, s_inv_lines = render_s_lines("S^-1(a)", a_vector, inverse=True)
    r_result, r_lines = render_r_lines(a_vector)
    r_inv_result, r_inv_lines = render_r_inv_lines(a_vector)
    l_result, l_lines = render_l_round_lines("L(a)", a_vector, inverse=False)
    l_inv_result, l_inv_lines = render_l_round_lines("L^-1(a)", a_vector, inverse=True)
    f_result, f_lines = render_f_lines(key, a_vector, b_vector)

    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Отчет по решению",
        "",
        "## Исходные данные",
        "",
        f"- source: {bytes_bin_str(source)}",
        f"- key: {bytes_bin_str(key)}",
        "",
    ]

    lines.extend(render_mapping_lines("b", "a", a_mapping))
    lines.extend(render_vector_lines("Вектор a", a_vector))
    lines.extend(render_mapping_lines("b", "b", b_mapping))
    lines.extend(render_vector_lines("Вектор b", b_vector))
    lines.extend(x_lines)
    lines.extend(s_lines)
    lines.extend(s_inv_lines)
    lines.extend(r_lines)
    lines.extend(r_inv_lines)
    lines.extend(l_lines)
    lines.extend(l_inv_lines)
    lines.extend(f_lines)
    lines.extend(
        render_final_hex_lines(
            source,
            key,
            a_vector,
            b_vector,
            x_result,
            s_result,
            s_inv_result,
            r_result,
            r_inv_result,
            l_result,
            l_inv_result,
            f_result,
        )
    )
    lines.extend(render_checks_lines(a_vector))

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

.vector-matrix {
  display: inline-grid;
  gap: 2px;
}

.vector-matrix-row {
  display: grid;
  grid-template-columns: repeat(4, max-content);
  gap: 8px;
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


def build_pdf_report(payload: dict[str, Any], simple: bool = False) -> tuple[str, str, bytes]:
    if simple:
        markdown = build_simple_markdown_report(payload)
    else:
        result = run_trace(payload)
        markdown = build_markdown_report(result, payload)
    pdf_bytes = markdown_to_pdf_bytes(markdown)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = "gost-simple-report" if simple else "gost-full-report"
    filename = f"{prefix}-{timestamp}.pdf"
    return filename, markdown, pdf_bytes


def build_pdf_report_from_result(
    payload: dict[str, Any],
    result: dict[str, Any],
    prefix: str,
) -> tuple[str, str, bytes]:
    markdown = build_markdown_report(result, payload)
    pdf_bytes = markdown_to_pdf_bytes(markdown)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{prefix}-{timestamp}.pdf"
    return filename, markdown, pdf_bytes
