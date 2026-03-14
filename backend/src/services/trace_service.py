from __future__ import annotations

import html
import re
from typing import Any

import pandas as pd


MOD_POLY_FULL = 0x1C3
MOD_POLY_LOW = 0xC3

PI = [
    252, 238, 221, 17, 207, 110, 49, 22, 251, 196, 250, 218, 35, 197, 4, 77,
    233, 119, 240, 219, 147, 46, 153, 186, 23, 54, 241, 187, 20, 205, 95, 193,
    249, 24, 101, 90, 226, 92, 239, 33, 129, 28, 60, 66, 139, 1, 142, 79,
    5, 132, 2, 174, 227, 106, 143, 160, 6, 11, 237, 152, 127, 212, 211, 31,
    235, 52, 44, 81, 234, 200, 72, 171, 242, 42, 104, 162, 253, 58, 206, 204,
    181, 112, 14, 86, 8, 12, 118, 18, 191, 114, 19, 71, 156, 183, 93, 135,
    21, 161, 150, 41, 16, 123, 154, 199, 243, 145, 120, 111, 157, 158, 178, 177,
    50, 117, 25, 61, 255, 53, 138, 126, 109, 84, 198, 128, 195, 189, 13, 87,
    223, 245, 36, 169, 62, 168, 67, 201, 215, 121, 214, 246, 124, 34, 185, 3,
    224, 15, 236, 222, 122, 148, 176, 188, 220, 232, 40, 80, 78, 51, 10, 74,
    167, 151, 96, 115, 30, 0, 98, 68, 26, 184, 56, 130, 100, 159, 38, 65,
    173, 69, 70, 146, 39, 94, 85, 47, 140, 163, 165, 125, 105, 213, 149, 59,
    7, 88, 179, 64, 134, 172, 29, 247, 48, 55, 107, 228, 136, 217, 231, 137,
    225, 27, 131, 73, 76, 63, 248, 254, 141, 83, 170, 144, 202, 216, 133, 97,
    32, 113, 103, 164, 45, 43, 9, 91, 203, 155, 37, 208, 190, 229, 108, 82,
    89, 166, 116, 210, 230, 244, 180, 192, 209, 102, 175, 194, 57, 75, 99, 182,
]

PI_INV = [0] * 256
for i, value in enumerate(PI):
    PI_INV[value] = i

L_COEFS = [148, 32, 133, 16, 194, 192, 1, 251, 1, 192, 194, 16, 133, 32, 148, 1]


def b8(value: int) -> str:
    return format(value & 0xFF, "08b")


def poly_str(value: int, width: int = 8) -> str:
    bits = format(value, f"0{width}b")
    terms: list[str] = []
    for idx, bit in enumerate(bits):
        if bit != "1":
            continue
        degree = width - 1 - idx
        if degree == 0:
            terms.append("1")
        elif degree == 1:
            terms.append("x")
        else:
            terms.append(f"x^{degree}")
    return " + ".join(terms) if terms else "0"


def bytes_hex_str(arr: list[int]) -> str:
    return " ".join(f"{x:02X}" for x in arr)


def bytes_bin_str(arr: list[int]) -> str:
    return " ".join(b8(x) for x in arr)


def _normalize_tokens(value: Any, field_name: str) -> list[str]:
    if isinstance(value, str):
        return value.replace(",", " ").split()
    if isinstance(value, list):
        return [str(item) for item in value]
    raise ValueError(f"Поле '{field_name}' должно быть строкой или массивом.")


def parse_hex_byte(token: str) -> int:
    prepared = token.strip().lower().replace("0x", "")
    if not re.fullmatch(r"[0-9a-f]{1,2}", prepared):
        raise ValueError(f"Некорректный байт: {token}")
    return int(prepared, 16)


def parse_hex_vector(value: Any, field_name: str) -> list[int]:
    tokens = _normalize_tokens(value, field_name)
    if len(tokens) != 16:
        raise ValueError(f"Поле '{field_name}' должно содержать ровно 16 байтов.")
    return [parse_hex_byte(token) for token in tokens]


def parse_mapping(value: Any, field_name: str) -> list[int]:
    tokens = _normalize_tokens(value, field_name)
    if len(tokens) != 16:
        raise ValueError(f"Поле '{field_name}' должно содержать ровно 16 индексов.")
    try:
        mapping = [int(token) for token in tokens]
    except ValueError as exc:
        raise ValueError(f"Поле '{field_name}' должно содержать целые числа.") from exc
    if any(item < 0 or item > 15 for item in mapping):
        raise ValueError(f"Поле '{field_name}' должно содержать индексы от 0 до 15.")
    return mapping


def block_text(text: str) -> dict[str, str]:
    safe = html.escape(text)
    return {"type": "text", "html": f"<p>{safe}</p>"}


def format_vector_cell(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    tokens = value.strip().split()
    if len(tokens) != 16:
        return html.escape(value)

    is_hex_vector = all(re.fullmatch(r"[0-9A-F]{2}", token) for token in tokens)
    is_bin_vector = all(re.fullmatch(r"[01]{8}", token) for token in tokens)
    if not (is_hex_vector or is_bin_vector):
        return html.escape(value)

    rows = []
    for index in range(0, 16, 4):
        row_tokens = tokens[index:index + 4]
        cells = "".join(f"<span class='vector-matrix-item'>{html.escape(token)}</span>" for token in row_tokens)
        rows.append(f"<span class='vector-matrix-row'>{cells}</span>")
    return f"<span class='vector-matrix'>{''.join(rows)}</span>"


def df_to_html(df: pd.DataFrame) -> str:
    rendered_df = df.copy()
    for column in rendered_df.columns:
        rendered_df[column] = rendered_df[column].map(format_vector_cell)
    return rendered_df.to_html(index=False, classes="trace-table", border=0, escape=False)


def block_table(df: pd.DataFrame, caption: str | None = None) -> dict[str, str]:
    html_table = df_to_html(df)
    if caption:
        safe_caption = html.escape(caption)
        html_table = f"<div class='table-caption'>{safe_caption}</div>{html_table}"
    return {"type": "table", "html": html_table}


def node(title: str, blocks: list[dict[str, str]] | None = None, steps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"title": title, "blocks": blocks or [], "steps": steps or []}


def vector_df(arr: list[int]) -> pd.DataFrame:
    rows = []
    for idx, value in enumerate(arr):
        rows.append(
            {
                "index": idx,
                "hex": f"{value:02X}",
                "bin": b8(value),
                "poly": poly_str(value, 8),
            }
        )
    return pd.DataFrame(rows)


def mapping_df(source: list[int], mapping: list[int], output_name: str) -> tuple[list[int], pd.DataFrame]:
    rows = []
    out: list[int] = []
    for idx, source_index in enumerate(mapping):
        value = source[source_index]
        out.append(value)
        rows.append(
            {
                f"{output_name}_index": idx,
                "берем из": f"b{source_index}",
                "hex": f"{value:02X}",
                "bin": b8(value),
                "poly": poly_str(value, 8),
            }
        )
    return out, pd.DataFrame(rows)


def xor_trace(left: list[int], right: list[int]) -> tuple[list[int], pd.DataFrame]:
    rows = []
    out: list[int] = []
    for idx, (a_val, b_val) in enumerate(zip(left, right)):
        result = a_val ^ b_val
        out.append(result)
        rows.append(
            {
                "i": idx,
                "left_hex": f"{a_val:02X}",
                "right_hex": f"{b_val:02X}",
                "left_bin": b8(a_val),
                "right_bin": b8(b_val),
                "xor_bin": b8(result),
                "xor_hex": f"{result:02X}",
                "xor_poly": poly_str(result, 8),
            }
        )
    return out, pd.DataFrame(rows)


def s_trace(arr: list[int], inverse: bool = False) -> tuple[list[int], pd.DataFrame]:
    rows = []
    out: list[int] = []
    table = PI_INV if inverse else PI
    for idx, value in enumerate(arr):
        mapped = table[value]
        out.append(mapped)
        rows.append(
            {
                "i": idx,
                "in_hex": f"{value:02X}",
                "in_bin": b8(value),
                "out_hex": f"{mapped:02X}",
                "out_bin": b8(mapped),
                "in_poly": poly_str(value, 8),
                "out_poly": poly_str(mapped, 8),
            }
        )
    return out, pd.DataFrame(rows)


def gf_mul_trace(a: int, b: int) -> tuple[int, pd.DataFrame]:
    rows = []
    result = 0
    aa = a & 0xFF
    bb = b & 0xFF
    for step in range(8):
        before = result
        bit = bb & 1
        if bit:
            result ^= aa

        high = (aa >> 7) & 1
        shifted = (aa << 1) & 0xFF
        if high:
            aa_next = shifted ^ MOD_POLY_LOW
            reduction = f"{b8(shifted)} XOR {b8(MOD_POLY_LOW)} = {b8(aa_next)}"
        else:
            aa_next = shifted
            reduction = b8(aa_next)

        rows.append(
            {
                "step": step,
                "a_cur": b8(aa),
                "b_cur": b8(bb),
                "LSB(b)": bit,
                "res_before": b8(before),
                "res_after": b8(result),
                "a<<1": b8(shifted),
                "high_bit(a)": high,
                "reduction": reduction,
                "a_next": b8(aa_next),
                "b_next": b8(bb >> 1),
            }
        )

        aa = aa_next
        bb >>= 1

    return result & 0xFF, pd.DataFrame(rows)


def gf_mul_fast(a: int, b: int) -> int:
    result = 0
    aa = a & 0xFF
    bb = b & 0xFF
    for _ in range(8):
        if bb & 1:
            result ^= aa
        high = aa & 0x80
        aa = (aa << 1) & 0xFF
        if high:
            aa ^= MOD_POLY_LOW
        bb >>= 1
    return result & 0xFF


def l_trace(arr: list[int], include_mul_bit_steps: bool) -> tuple[int, list[dict[str, str]], list[dict[str, Any]]]:
    products: list[int] = []
    product_rows = []
    mul_steps: list[dict[str, Any]] = []

    for idx, (coef, value) in enumerate(zip(L_COEFS, arr)):
        product, mul_df = gf_mul_trace(coef, value)
        products.append(product)
        product_rows.append(
            {
                "i": idx,
                "coef_hex": f"{coef:02X}",
                "coef_bin": b8(coef),
                "a_hex": f"{value:02X}",
                "a_bin": b8(value),
                "prod_hex": f"{product:02X}",
                "prod_bin": b8(product),
                "prod_poly": poly_str(product, 8),
            }
        )
        if include_mul_bit_steps:
            mul_steps.append(
                node(
                    title=f"Умножение #{idx + 1}: {coef:02X} * {value:02X}",
                    blocks=[
                        block_text(
                            f"{coef:02X} ({poly_str(coef, 8)}) × {value:02X} ({poly_str(value, 8)}) = {product:02X}"
                        ),
                        block_table(mul_df, "Побитовые шаги умножения в GF(2^8)"),
                    ],
                )
            )

    xor_rows = []
    acc = 0
    for idx, term in enumerate(products):
        before = acc
        acc ^= term
        xor_rows.append(
            {
                "step": idx,
                "term_hex": f"{term:02X}",
                "term_bin": b8(term),
                "acc_before": b8(before),
                "acc_after": b8(acc),
                "acc_after_hex": f"{acc:02X}",
                "acc_poly": poly_str(acc, 8),
            }
        )

    blocks = [
        block_text("l(a15..a0) вычисляется как XOR 16 произведений коэффициентов на байты вектора."),
        block_table(pd.DataFrame(product_rows), "Таблица произведений для l"),
        block_table(pd.DataFrame(xor_rows), "Пошаговый XOR произведений"),
        block_text(f"Итог l = {acc:02X} ({b8(acc)}; {poly_str(acc, 8)})"),
    ]
    return acc, blocks, mul_steps


def r_step(arr: list[int], include_mul_bit_steps: bool) -> tuple[list[int], list[dict[str, Any]]]:
    l_value, l_blocks, l_mul_steps = l_trace(arr, include_mul_bit_steps=include_mul_bit_steps)
    result = [l_value] + arr[:15]
    move_rows = []
    for idx, value in enumerate(result):
        move_rows.append(
            {
                "new_index": idx,
                "value_hex": f"{value:02X}",
                "value_bin": b8(value),
                "source": "l(...)" if idx == 0 else f"old[{idx - 1}]",
            }
        )

    steps = [
        node("Шаг 1: Входной вектор", blocks=[block_table(vector_df(arr), "Вектор до преобразования")]),
        node("Шаг 2: Вычисление l(a15..a0)", blocks=l_blocks, steps=l_mul_steps),
        node(
            "Шаг 3: Сборка результата R(a)",
            blocks=[block_table(pd.DataFrame(move_rows), "Перестановка после вычисления l"), block_text(f"R(a) = {bytes_hex_str(result)}")],
        ),
    ]
    return result, steps


def r_inv_step(arr: list[int], include_mul_bit_steps: bool) -> tuple[list[int], list[dict[str, Any]]]:
    shifted = arr[1:] + [arr[0]]
    l_value, l_blocks, l_mul_steps = l_trace(shifted, include_mul_bit_steps=include_mul_bit_steps)
    result = arr[1:] + [l_value]
    move_rows = []
    for idx, value in enumerate(result):
        move_rows.append(
            {
                "new_index": idx,
                "value_hex": f"{value:02X}",
                "value_bin": b8(value),
                "source": f"old[{idx + 1}]" if idx < 15 else "l(shifted)",
            }
        )

    steps = [
        node("Шаг 1: Входной вектор", blocks=[block_table(vector_df(arr), "Вектор до преобразования")]),
        node("Шаг 2: Формирование shifted", blocks=[block_table(vector_df(shifted), "shifted = a1..a15 || a0")]),
        node("Шаг 3: Вычисление l(shifted)", blocks=l_blocks, steps=l_mul_steps),
        node(
            "Шаг 4: Сборка результата R^-1(a)",
            blocks=[block_table(pd.DataFrame(move_rows), "Перестановка после вычисления l"), block_text(f"R^-1(a) = {bytes_hex_str(result)}")],
        ),
    ]
    return result, steps


def r_fast(arr: list[int]) -> list[int]:
    acc = 0
    for coef, value in zip(L_COEFS, arr):
        acc ^= gf_mul_fast(coef, value)
    return [acc & 0xFF] + arr[:15]


def r_inv_fast(arr: list[int]) -> list[int]:
    shifted = arr[1:] + [arr[0]]
    acc = 0
    for coef, value in zip(L_COEFS, shifted):
        acc ^= gf_mul_fast(coef, value)
    return arr[1:] + [acc & 0xFF]


def l_fast(arr: list[int]) -> list[int]:
    cur = arr[:]
    for _ in range(16):
        cur = r_fast(cur)
    return cur


def l_inv_fast(arr: list[int]) -> list[int]:
    cur = arr[:]
    for _ in range(16):
        cur = r_inv_fast(cur)
    return cur


def s_fast(arr: list[int], inverse: bool = False) -> list[int]:
    box = PI_INV if inverse else PI
    return [box[value] for value in arr]


def l_action(arr: list[int], inverse: bool = False) -> tuple[list[int], dict[str, Any]]:
    cur = arr[:]
    rounds: list[dict[str, Any]] = []
    history_rows = []
    transformer = r_inv_step if inverse else r_step
    caption = "L^-1(a) = (R^-1)^16(a)" if inverse else "L(a) = R^16(a)"

    for idx in range(16):
        before = cur[:]
        cur, round_steps = transformer(cur, include_mul_bit_steps=False)
        rounds.append(node(title=f"Раунд {idx + 1}", steps=round_steps))
        history_rows.append(
            {
                "step": idx + 1,
                "before_hex": bytes_hex_str(before),
                "after_hex": bytes_hex_str(cur),
                "after_bin": bytes_bin_str(cur),
            }
        )

    action = node(
        title=caption,
        blocks=[
            block_text("Промежуточные состояния после каждого раунда:"),
            block_table(pd.DataFrame(history_rows), "История состояний"),
            block_text(f"Итог: {bytes_hex_str(cur)}"),
        ],
        steps=rounds,
    )
    return cur, action


def f_action(k: list[int], a: list[int], b: list[int]) -> tuple[tuple[list[int], list[int]], dict[str, Any]]:
    x_result, x_df = xor_trace(k, a)
    s_result, s_df = s_trace(x_result, inverse=False)
    l_result, l_step_action = l_action(s_result, inverse=False)
    first_result, first_df = xor_trace(l_result, b)
    second_result = a[:]

    action = node(
        title="F[k](a, b) = (LSX[k](a) XOR b, a)",
        blocks=[
            block_text(f"Первый выход: {bytes_hex_str(first_result)}"),
            block_text(f"Второй выход: {bytes_hex_str(second_result)}"),
        ],
        steps=[
            node(
                title="Шаг 1: X[k](a) = k XOR a",
                blocks=[block_table(x_df, "XOR ключа и вектора a"), block_text(f"X = {bytes_hex_str(x_result)}")],
            ),
            node(
                title="Шаг 2: S(X)",
                blocks=[block_table(s_df, "Подстановка по S-box"), block_text(f"S(X) = {bytes_hex_str(s_result)}")],
            ),
            node(
                title="Шаг 3: L(S(X))",
                blocks=l_step_action["blocks"],
                steps=l_step_action["steps"],
            ),
            node(
                title="Шаг 4: LSX XOR b",
                blocks=[block_table(first_df, "XOR результата LSX и вектора b"), block_text(f"F.first = {bytes_hex_str(first_result)}")],
            ),
            node(
                title="Шаг 5: Второй выход",
                blocks=[block_table(vector_df(second_result), "Второй выход F равен исходному a")],
            ),
        ],
    )
    return (first_result, second_result), action


def run_trace(payload: dict[str, Any]) -> dict[str, Any]:
    source = parse_hex_vector(payload.get("sourceBytes", ""), "sourceBytes")
    a_mapping = parse_mapping(payload.get("aMapping", ""), "aMapping")
    b_mapping = parse_mapping(payload.get("bMapping", ""), "bMapping")
    key = parse_hex_vector(payload.get("keyBytes", ""), "keyBytes")

    actions: list[dict[str, Any]] = []

    actions.append(
        node(
            title="Исходные данные",
            blocks=[
                block_text("Введенные пользователем векторы source и key:"),
                block_table(vector_df(source), "source b0..b15"),
                block_table(vector_df(key), "key k0..k15"),
            ],
        )
    )

    a_vector, a_df = mapping_df(source, a_mapping, output_name="a")
    actions.append(
        node(
            title="Построение вектора a по индексам",
            blocks=[
                block_table(a_df, "Таблица соответствия a_i = b_j"),
                block_text(f"a = {bytes_hex_str(a_vector)}"),
            ],
        )
    )

    b_vector, b_df = mapping_df(source, b_mapping, output_name="b")
    actions.append(
        node(
            title="Построение вектора b по индексам",
            blocks=[
                block_table(b_df, "Таблица соответствия b_i = source_j"),
                block_text(f"b = {bytes_hex_str(b_vector)}"),
            ],
        )
    )

    x_result, x_df = xor_trace(key, a_vector)
    actions.append(
        node(
            title="X[k](a) = k XOR a",
            blocks=[block_table(x_df, "Побайтовый XOR"), block_text(f"X[k](a) = {bytes_hex_str(x_result)}")],
        )
    )

    s_result, s_df = s_trace(a_vector, inverse=False)
    actions.append(
        node(title="S(a)", blocks=[block_table(s_df, "Подстановка по S-box"), block_text(f"S(a) = {bytes_hex_str(s_result)}")])
    )

    s_inv_result, s_inv_df = s_trace(a_vector, inverse=True)
    actions.append(
        node(
            title="S^-1(a)",
            blocks=[block_table(s_inv_df, "Подстановка по обратному S-box"), block_text(f"S^-1(a) = {bytes_hex_str(s_inv_result)}")],
        )
    )

    r_result, r_steps = r_step(a_vector, include_mul_bit_steps=True)
    actions.append(node(title="R(a)", blocks=[block_text(f"R(a) = {bytes_hex_str(r_result)}")], steps=r_steps))

    r_inv_result, r_inv_steps = r_inv_step(a_vector, include_mul_bit_steps=True)
    actions.append(node(title="R^-1(a)", blocks=[block_text(f"R^-1(a) = {bytes_hex_str(r_inv_result)}")], steps=r_inv_steps))

    l_result, l_details = l_action(a_vector, inverse=False)
    actions.append(node(title="L(a) = R^16(a)", blocks=l_details["blocks"], steps=l_details["steps"]))

    l_inv_result, l_inv_details = l_action(a_vector, inverse=True)
    actions.append(node(title="L^-1(a) = (R^-1)^16(a)", blocks=l_inv_details["blocks"], steps=l_inv_details["steps"]))

    (f_first, f_second), f_details = f_action(key, a_vector, b_vector)
    actions.append(node(title="F[k](a, b)", blocks=f_details["blocks"], steps=f_details["steps"]))

    checks_df = pd.DataFrame(
        [
            {"Проверка": "S^-1(S(a)) = a", "Результат": s_fast(s_fast(a_vector, inverse=False), inverse=True) == a_vector},
            {"Проверка": "R^-1(R(a)) = a", "Результат": r_inv_fast(r_fast(a_vector)) == a_vector},
            {"Проверка": "L^-1(L(a)) = a", "Результат": l_inv_fast(l_fast(a_vector)) == a_vector},
        ]
    )
    actions.append(node(title="Проверки обратимости", blocks=[block_table(checks_df)]))

    summary_rows = [
        {"Преобразование": "X[k](a)", "HEX": bytes_hex_str(x_result), "BIN": bytes_bin_str(x_result)},
        {"Преобразование": "S(a)", "HEX": bytes_hex_str(s_result), "BIN": bytes_bin_str(s_result)},
        {"Преобразование": "S^-1(a)", "HEX": bytes_hex_str(s_inv_result), "BIN": bytes_bin_str(s_inv_result)},
        {"Преобразование": "R(a)", "HEX": bytes_hex_str(r_result), "BIN": bytes_bin_str(r_result)},
        {"Преобразование": "R^-1(a)", "HEX": bytes_hex_str(r_inv_result), "BIN": bytes_bin_str(r_inv_result)},
        {"Преобразование": "L(a)", "HEX": bytes_hex_str(l_result), "BIN": bytes_bin_str(l_result)},
        {"Преобразование": "L^-1(a)", "HEX": bytes_hex_str(l_inv_result), "BIN": bytes_bin_str(l_inv_result)},
        {"Преобразование": "F first", "HEX": bytes_hex_str(f_first), "BIN": bytes_bin_str(f_first)},
        {"Преобразование": "F second", "HEX": bytes_hex_str(f_second), "BIN": bytes_bin_str(f_second)},
    ]
    summary_df = pd.DataFrame(summary_rows)
    actions.append(node(title="Финальная сводка", blocks=[block_table(summary_df)]))

    return {
        "actions": actions,
        "summaryTableHtml": df_to_html(summary_df),
        "checksTableHtml": df_to_html(checks_df),
    }
