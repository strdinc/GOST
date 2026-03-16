from __future__ import annotations

from typing import Any

import pandas as pd

from src.services.trace_service import (
    block_table,
    block_text,
    bytes_bin_str,
    bytes_hex_str,
    df_to_html,
    l_fast,
    mapping_df,
    node,
    parse_hex_vector,
    parse_mapping,
    s_trace,
    vector_df,
    xor_trace,
)


def vec128(value: int) -> list[int]:
    return [0] * 15 + [value & 0xFF]


def f_compact_action(k: list[int], a: list[int], b: list[int]) -> tuple[tuple[list[int], list[int]], dict[str, Any]]:
    x_result, x_df = xor_trace(k, a)
    s_result, s_df = s_trace(x_result, inverse=False)
    l_result = l_fast(s_result)
    first_result, first_df = xor_trace(l_result, b)
    second_result = a[:]

    l_summary_df = pd.DataFrame(
        [
            {
                "input_hex": bytes_hex_str(s_result),
                "output_hex": bytes_hex_str(l_result),
                "output_bin": bytes_bin_str(l_result),
            }
        ]
    )

    action = node(
        title="F[k](a, b) = (LSX[k](a) XOR b, a)",
        blocks=[
            block_text(f"k = {bytes_hex_str(k)}"),
            block_text(f"a = {bytes_hex_str(a)}"),
            block_text(f"b = {bytes_hex_str(b)}"),
            block_text(f"F.first = {bytes_hex_str(first_result)}"),
            block_text(f"F.second = {bytes_hex_str(second_result)}"),
        ],
        steps=[
            node(
                title="Шаг 1: X[k](a)",
                blocks=[
                    block_table(x_df, "Побайтовый XOR константы и левой половины"),
                    block_text(f"X = {bytes_hex_str(x_result)}"),
                ],
            ),
            node(
                title="Шаг 2: S(X)",
                blocks=[
                    block_table(s_df, "Подстановка по S-box"),
                    block_text(f"S(X) = {bytes_hex_str(s_result)}"),
                ],
            ),
            node(
                title="Шаг 3: L(S(X))",
                blocks=[
                    block_table(l_summary_df, "Результат линейного преобразования L"),
                    block_text(f"L(S(X)) = {bytes_hex_str(l_result)}"),
                ],
            ),
            node(
                title="Шаг 4: LSX XOR b",
                blocks=[
                    block_table(first_df, "XOR результата LSX и правой половины"),
                    block_text(f"Новая левая половина = {bytes_hex_str(first_result)}"),
                ],
            ),
            node(
                title="Шаг 5: Перенос старой левой половины",
                blocks=[block_table(vector_df(second_result), "Новая правая половина")],
            ),
        ],
    )
    return (first_result, second_result), action


def run_key_schedule_trace(payload: dict[str, Any]) -> dict[str, Any]:
    source = parse_hex_vector(payload.get("sourceBytes", ""), "sourceBytes")
    a_mapping = parse_mapping(payload.get("aMapping", ""), "aMapping")
    b_mapping = parse_mapping(payload.get("bMapping", ""), "bMapping")

    actions: list[dict[str, Any]] = []

    actions.append(
        node(
            title="Исходные данные",
            blocks=[
                block_text("Лабораторная 4 использует те же исходные данные, что и лабораторная 3."),
                block_table(vector_df(source), "source b0..b15"),
            ],
        )
    )

    a_vector, a_df = mapping_df(source, a_mapping, output_name="a")
    b_vector, b_df = mapping_df(source, b_mapping, output_name="b")

    actions.append(
        node(
            title="Построение половин мастер-ключа",
            blocks=[
                block_table(a_df, "Построение a"),
                block_table(b_df, "Построение b"),
                block_text(f"K1 = a = {bytes_hex_str(a_vector)}"),
                block_text(f"K2 = b = {bytes_hex_str(b_vector)}"),
                block_text(f"Мастер-ключ K = K1 || K2 = {bytes_hex_str(a_vector)} || {bytes_hex_str(b_vector)}"),
            ],
        )
    )

    constants: list[list[int]] = []
    constant_rows = []
    constant_steps: list[dict[str, Any]] = []
    for index in range(1, 33):
        vec = vec128(index)
        constant = l_fast(vec)
        constants.append(constant)
        constant_rows.append(
            {
                "i": index,
                "Vec128(i)": bytes_hex_str(vec),
                "Ci_hex": bytes_hex_str(constant),
                "Ci_bin": bytes_bin_str(constant),
            }
        )
        constant_steps.append(
            node(
                title=f"C{index}",
                blocks=[
                    block_table(vector_df(vec), f"Vec128({index})"),
                    block_table(vector_df(constant), f"C{index} = L(Vec128({index}))"),
                ],
            )
        )

    actions.append(
        node(
            title="Генерация итерационных констант C1..C32",
            blocks=[
                block_text("Для каждой константы берется Vec128(i), после чего применяется преобразование L."),
                block_table(pd.DataFrame(constant_rows), "Таблица констант Ci"),
            ],
            steps=constant_steps,
        )
    )

    round_keys: list[list[int]] = [a_vector[:], b_vector[:]]
    left = a_vector[:]
    right = b_vector[:]
    generation_steps: list[dict[str, Any]] = []

    for group_index in range(4):
        group_steps: list[dict[str, Any]] = []
        constant_slice = constants[group_index * 8:(group_index + 1) * 8]

        for offset, constant in enumerate(constant_slice, start=1):
            call_input_left = left[:]
            call_input_right = right[:]
            (left, right), f_details = f_compact_action(constant, left, right)
            group_steps.append(
                node(
                    title=f"Применение F с C{group_index * 8 + offset}",
                    blocks=[
                        block_text(f"Константа: {bytes_hex_str(constant)}"),
                        block_text(f"Входная пара: ({bytes_hex_str(call_input_left)}, {bytes_hex_str(call_input_right)})"),
                        block_text(f"Выходная пара: ({bytes_hex_str(left)}, {bytes_hex_str(right)})"),
                    ],
                    steps=[f_details],
                )
            )

        round_keys.extend([left[:], right[:]])
        pair_df = pd.DataFrame(
            [
                {"key": f"K{group_index * 2 + 3}", "hex": bytes_hex_str(left), "bin": bytes_bin_str(left)},
                {"key": f"K{group_index * 2 + 4}", "hex": bytes_hex_str(right), "bin": bytes_bin_str(right)},
            ]
        )
        generation_steps.append(
            node(
                title=f"Блок {group_index + 1}: получение K{group_index * 2 + 3} и K{group_index * 2 + 4}",
                blocks=[
                    block_text(
                        f"Начальная пара блока: ({bytes_hex_str(round_keys[group_index * 2])}, {bytes_hex_str(round_keys[group_index * 2 + 1])})"
                    ),
                    block_table(pair_df, "Результат после 8 применений F"),
                ],
                steps=group_steps,
            )
        )

    key_rows = [
        {"Раундовый ключ": f"K{index}", "HEX": bytes_hex_str(key), "BIN": bytes_bin_str(key)}
        for index, key in enumerate(round_keys, start=1)
    ]
    keys_df = pd.DataFrame(key_rows)

    actions.append(
        node(
            title="Развертка мастер-ключа K -> K1..K10",
            blocks=[
                block_text("После начального разбиения K1 и K2 еще 8 ключей получаются четырьмя блоками по 8 вызовов F."),
                block_table(keys_df, "Все раундовые ключи"),
            ],
            steps=generation_steps,
        )
    )

    checks_df = pd.DataFrame(
        [
            {"Проверка": "Количество констант", "Результат": len(constants) == 32},
            {"Проверка": "Количество раундовых ключей", "Результат": len(round_keys) == 10},
            {"Проверка": "K1 совпадает с a", "Результат": round_keys[0] == a_vector},
            {"Проверка": "K2 совпадает с b", "Результат": round_keys[1] == b_vector},
        ]
    )
    actions.append(node(title="Проверки", blocks=[block_table(checks_df)]))

    summary_df = keys_df.copy()
    actions.append(node(title="Финальная сводка", blocks=[block_table(summary_df)]))

    return {
        "actions": actions,
        "summaryTableHtml": df_to_html(summary_df),
        "checksTableHtml": df_to_html(checks_df),
    }
