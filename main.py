import re
import pandas as pd

pd.set_option("display.max_rows", 1000)
pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 300)
pd.set_option("display.max_colwidth", 200)

# =========================================================
# Поле GF(2^8)
# p(x) = x^8 + x^7 + x^6 + x + 1
# =========================================================

MOD_POLY_FULL = 0x1C3
MOD_POLY_LOW = 0xC3

# =========================================================
# S-box Кузнечика
# =========================================================

PI = [
    252, 238, 221,  17, 207, 110,  49,  22, 251, 196, 250, 218,  35, 197,   4,  77,
    233, 119, 240, 219, 147,  46, 153, 186,  23,  54, 241, 187,  20, 205,  95, 193,
    249,  24, 101,  90, 226,  92, 239,  33, 129,  28,  60,  66, 139,   1, 142,  79,
      5, 132,   2, 174, 227, 106, 143, 160,   6,  11, 237, 152, 127, 212, 211,  31,
    235,  52,  44,  81, 234, 200,  72, 171, 242,  42, 104, 162, 253,  58, 206, 204,
    181, 112,  14,  86,   8,  12, 118,  18, 191, 114,  19,  71, 156, 183,  93, 135,
     21, 161, 150,  41,  16, 123, 154, 199, 243, 145, 120, 111, 157, 158, 178, 177,
     50, 117,  25,  61, 255,  53, 138, 126, 109,  84, 198, 128, 195, 189,  13,  87,
    223, 245,  36, 169,  62, 168,  67, 201, 215, 121, 214, 246, 124,  34, 185,   3,
    224,  15, 236, 222, 122, 148, 176, 188, 220, 232,  40,  80,  78,  51,  10,  74,
    167, 151,  96, 115,  30,   0,  98,  68,  26, 184,  56, 130, 100, 159,  38,  65,
    173,  69,  70, 146,  39,  94,  85,  47, 140, 163, 165, 125, 105, 213, 149,  59,
      7,  88, 179,  64, 134, 172,  29, 247,  48,  55, 107, 228, 136, 217, 231, 137,
    225,  27, 131,  73,  76,  63, 248, 254, 141,  83, 170, 144, 202, 216, 133,  97,
     32, 113, 103, 164,  45,  43,   9,  91, 203, 155,  37, 208, 190, 229, 108,  82,
     89, 166, 116, 210, 230, 244, 180, 192, 209, 102, 175, 194,  57,  75,  99, 182
]

PI_INV = [0] * 256
for i, v in enumerate(PI):
    PI_INV[v] = i

L_COEFS = [148, 32, 133, 16, 194, 192, 1, 251, 1, 192, 194, 16, 133, 32, 148, 1]

# =========================================================
# Форматирование
# =========================================================

def b8(x: int) -> str:
    return format(x & 0xFF, "08b")

def poly_str(x: int, width: int = 8) -> str:
    bits = format(x, f"0{width}b")
    terms = []
    for i, bit in enumerate(bits):
        if bit == "1":
            p = width - 1 - i
            if p == 0:
                terms.append("1")
            elif p == 1:
                terms.append("x")
            else:
                terms.append(f"x^{p}")
    return " + ".join(terms) if terms else "0"

def bytes_bin_str(arr):
    return " ".join(b8(x) for x in arr)

def bytes_hex_str(arr):
    return " ".join(f"{x:02X}" for x in arr)

def title(txt: str):
    print("\n" + "=" * 120)
    print(txt)
    print("=" * 120)

def show_vector(name: str, arr):
    print(f"{name}:")
    rows = []
    for i, x in enumerate(arr):
        rows.append({
            "index": i,
            "hex": f"{x:02X}",
            "bin": b8(x),
            "poly": poly_str(x, 8)
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print(f"\n{name} hex : {bytes_hex_str(arr)}")
    print(f"{name} bin : {bytes_bin_str(arr)}")

# =========================================================
# Ввод
# =========================================================

def parse_hex_byte(token: str) -> int:
    token = token.strip().lower().replace("0x", "")
    if not re.fullmatch(r"[0-9a-f]{1,2}", token):
        raise ValueError(f"Некорректный байт: {token}")
    return int(token, 16)

def input_16_bytes(prompt: str):
    while True:
        print(prompt)
        print("Введи 16 байтов через пробел, например:")
        print("55 65 51 33 4D 95 59 C7 93 8C BD E3 D6 AB 2F 79")
        s = input(">> ").strip()
        parts = s.split()
        if len(parts) != 16:
            print("Нужно ровно 16 байтов. Не 15, не 17. Люди и тут умудряются промахнуться.\n")
            continue
        try:
            arr = [parse_hex_byte(x) for x in parts]
            return arr
        except Exception as e:
            print(f"Ошибка: {e}\n")

def input_mapping(name="a"):
    while True:
        print(f"\nВведи отображение для {name}0..{name}15.")
        print("Формат: 16 чисел через пробел, где каждое число это индекс bj.")
        print(f"Например, если {name}0=b3, {name}1=b13, {name}2=b14, ...")
        print("то ввод будет:")
        print("3 13 14 11 4 10 15 9 1 0 12 2 5 8 6 7")
        s = input(">> ").strip()
        parts = s.split()
        if len(parts) != 16:
            print("Нужно ровно 16 индексов.\n")
            continue
        try:
            mapping = [int(x) for x in parts]
            if any(x < 0 or x > 15 for x in mapping):
                raise ValueError("Индексы должны быть от 0 до 15")
            return mapping
        except Exception as e:
            print(f"Ошибка: {e}\n")

def input_yes_no(prompt: str) -> bool:
    while True:
        s = input(f"{prompt} [y/n]: ").strip().lower()
        if s in ("y", "yes", "д", "да"):
            return True
        if s in ("n", "no", "н", "нет"):
            return False
        print("Введи y или n.\n")

# =========================================================
# Сборка вектора по отображению
# =========================================================

def build_from_mapping(b_bytes, mapping, out_name="a"):
    title(f"Построение вектора {out_name} по таблице отображения")
    rows = []
    out = []
    for i, bj in enumerate(mapping):
        val = b_bytes[bj]
        out.append(val)
        rows.append({
            f"{out_name}_index": i,
            "берём из": f"b{bj}",
            "hex": f"{val:02X}",
            "bin": b8(val),
            "poly": poly_str(val, 8)
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print(f"\n{out_name} hex : {bytes_hex_str(out)}")
    print(f"{out_name} bin : {bytes_bin_str(out)}")
    return out

# =========================================================
# XOR
# =========================================================

def xor_bytes_verbose(a_bytes, b_bytes, label):
    title(label)
    rows = []
    result = []
    for i, (a, b) in enumerate(zip(a_bytes, b_bytes)):
        r = a ^ b
        result.append(r)
        rows.append({
            "i": i,
            "left_hex": f"{a:02X}",
            "right_hex": f"{b:02X}",
            "left_bin": b8(a),
            "right_bin": b8(b),
            "xor_bin": b8(r),
            "xor_hex": f"{r:02X}",
            "xor_poly": poly_str(r, 8)
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\nРезультат:")
    print(bytes_bin_str(result))
    return result

# =========================================================
# Умножение GF(2^8)
# =========================================================

def gf_mul_verbose(a: int, b: int, label="Умножение в GF(2^8)") -> int:
    title(label)
    print(f"a = {a:02X} = {b8(a)} = {poly_str(a, 8)}")
    print(f"b = {b:02X} = {b8(b)} = {poly_str(b, 8)}")
    print(f"Модульный полином: {poly_str(MOD_POLY_FULL, 9)}")

    rows = []
    res = 0
    aa = a
    bb = b

    for step in range(8):
        res_before = res
        bit = bb & 1
        if bit:
            res ^= aa

        high = (aa >> 7) & 1
        shifted = (aa << 1) & 0xFF
        if high:
            aa_next = shifted ^ MOD_POLY_LOW
            reduction = f"{b8(shifted)} XOR {b8(MOD_POLY_LOW)} = {b8(aa_next)}"
        else:
            aa_next = shifted
            reduction = f"{b8(aa_next)}"

        rows.append({
            "step": step,
            "a_cur": b8(aa),
            "b_cur": b8(bb),
            "LSB(b)": bit,
            "res_before": b8(res_before),
            "res_after": b8(res),
            "a<<1": b8(shifted),
            "high_bit(a)": high,
            "reduction": reduction,
            "a_next": b8(aa_next),
            "b_next": b8(bb >> 1),
        })

        aa = aa_next
        bb >>= 1

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print(f"\nИтог: {b8(a)} · {b8(b)} = {b8(res)}")
    print(f"Итог hex: {res:02X}")
    print(f"Итог poly: {poly_str(res, 8)}")
    return res

# =========================================================
# X, S, S^-1
# =========================================================

def X_verbose(k_bytes, a_bytes):
    return xor_bytes_verbose(k_bytes, a_bytes, "Преобразование X[k](a) = k XOR a")

def S_verbose(a_bytes):
    title("Преобразование S(a)")
    rows = []
    result = []
    for i, x in enumerate(a_bytes):
        y = PI[x]
        result.append(y)
        rows.append({
            "i": i,
            "in_hex": f"{x:02X}",
            "in_bin": b8(x),
            "out_hex": f"{y:02X}",
            "out_bin": b8(y),
            "in_poly": poly_str(x, 8),
            "out_poly": poly_str(y, 8),
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\nРезультат S(a):")
    print(bytes_bin_str(result))
    return result

def S_inv_verbose(a_bytes):
    title("Преобразование S^-1(a)")
    rows = []
    result = []
    for i, x in enumerate(a_bytes):
        y = PI_INV[x]
        result.append(y)
        rows.append({
            "i": i,
            "in_hex": f"{x:02X}",
            "in_bin": b8(x),
            "out_hex": f"{y:02X}",
            "out_bin": b8(y),
            "in_poly": poly_str(x, 8),
            "out_poly": poly_str(y, 8),
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\nРезультат S^-1(a):")
    print(bytes_bin_str(result))
    return result

# =========================================================
# l-функция
# =========================================================

def l_verbose(a_bytes):
    title("Вычисление l(a15,...,a0)")
    rows = []
    terms = []

    for i in range(16):
        coef = L_COEFS[i]
        val = a_bytes[i]
        prod = gf_mul_verbose(coef, val, label=f"Шаг {i}: умножение коэффициента на байт")
        terms.append(prod)
        rows.append({
            "i": i,
            "coef_hex": f"{coef:02X}",
            "coef_bin": b8(coef),
            "a_hex": f"{val:02X}",
            "a_bin": b8(val),
            "prod_hex": f"{prod:02X}",
            "prod_bin": b8(prod),
            "prod_poly": poly_str(prod, 8)
        })

    title("Таблица всех произведений для l")
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    title("Пошаговый XOR произведений в l")
    xor_rows = []
    acc = 0
    for i, t in enumerate(terms):
        before = acc
        acc ^= t
        xor_rows.append({
            "step": i,
            "term_hex": f"{t:02X}",
            "term_bin": b8(t),
            "acc_before": b8(before),
            "acc_after": b8(acc),
            "acc_after_hex": f"{acc:02X}",
            "acc_poly": poly_str(acc, 8),
        })
    df2 = pd.DataFrame(xor_rows)
    print(df2.to_string(index=False))

    print(f"\nИтог l = {acc:02X} = {b8(acc)} = {poly_str(acc, 8)}")
    return acc

# =========================================================
# R, R^-1, L, L^-1
# =========================================================

def R_verbose(a_bytes):
    title("Преобразование R(a)")
    show_vector("R input", a_bytes)
    lval = l_verbose(a_bytes)
    result = [lval] + a_bytes[:15]

    rows = []
    for i, x in enumerate(result):
        rows.append({
            "new_index": i,
            "value_hex": f"{x:02X}",
            "value_bin": b8(x),
            "source": "l(...)" if i == 0 else f"old[{i-1}]"
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\nR(a):")
    print(bytes_bin_str(result))
    return result

def R_inv_verbose(a_bytes):
    title("Преобразование R^-1(a)")
    show_vector("R^-1 input", a_bytes)

    shifted = a_bytes[1:] + [a_bytes[0]]
    print("\nВектор для вычисления l в R^-1:")
    print(bytes_bin_str(shifted))

    lval = l_verbose(shifted)
    result = a_bytes[1:] + [lval]

    rows = []
    for i, x in enumerate(result):
        rows.append({
            "new_index": i,
            "value_hex": f"{x:02X}",
            "value_bin": b8(x),
            "source": f"old[{i+1}]" if i < 15 else "l(shifted)"
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\nR^-1(a):")
    print(bytes_bin_str(result))
    return result

def L_verbose(a_bytes):
    title("Преобразование L(a) = R^16(a)")
    cur = a_bytes[:]
    rows = []
    for i in range(16):
        print(f"\n--- Шаг L: {i+1}/16 ---")
        cur = R_verbose(cur)
        rows.append({
            "step": i + 1,
            "state_hex": bytes_hex_str(cur),
            "state_bin": bytes_bin_str(cur)
        })
    df = pd.DataFrame(rows)
    title("Промежуточные состояния L")
    print(df.to_string(index=False))
    print("\nИтог L(a):")
    print(bytes_bin_str(cur))
    return cur

def L_inv_verbose(a_bytes):
    title("Преобразование L^-1(a) = (R^-1)^16(a)")
    cur = a_bytes[:]
    rows = []
    for i in range(16):
        print(f"\n--- Шаг L^-1: {i+1}/16 ---")
        cur = R_inv_verbose(cur)
        rows.append({
            "step": i + 1,
            "state_hex": bytes_hex_str(cur),
            "state_bin": bytes_bin_str(cur)
        })
    df = pd.DataFrame(rows)
    title("Промежуточные состояния L^-1")
    print(df.to_string(index=False))
    print("\nИтог L^-1(a):")
    print(bytes_bin_str(cur))
    return cur

# =========================================================
# LSX и F
# =========================================================

def LSX_verbose(k_bytes, a_bytes):
    title("Вычисление LSX[k](a) = L(S(X[k](a)))")
    x = X_verbose(k_bytes, a_bytes)
    s = S_verbose(x)
    l = L_verbose(s)
    return l

def F_verbose(k_bytes, a_bytes, b_bytes):
    title("Преобразование F[k](a, b) = (LSX[k](a) XOR b, a)")
    lsx = LSX_verbose(k_bytes, a_bytes)
    first = xor_bytes_verbose(lsx, b_bytes, "Первый выход F: LSX[k](a) XOR b")
    second = a_bytes[:]

    print("\nВторой выход F:")
    print(bytes_bin_str(second))
    return first, second

# =========================================================
# Проверки
# =========================================================

def check_equal(name, left, right):
    title(f"Проверка: {name}")
    df = pd.DataFrame({
        "i": list(range(len(left))),
        "left_hex": [f"{x:02X}" for x in left],
        "right_hex": [f"{x:02X}" for x in right],
        "left_bin": [b8(x) for x in left],
        "right_bin": [b8(x) for x in right],
        "equal": [l == r for l, r in zip(left, right)]
    })
    print(df.to_string(index=False))
    print("\nРезультат:", left == right)

# =========================================================
# MAIN
# =========================================================

def main():
    title("ВВОД ИСХОДНЫХ ДАННЫХ")

    b_source = input_16_bytes("Введи 16 исходных байтов b0..b15:")

    use_mapping_for_a = input_yes_no("Собрать вектор a из b по таблице?")
    if use_mapping_for_a:
        a_mapping = input_mapping("a")
        a = build_from_mapping(b_source, a_mapping, "a")
    else:
        a = input_16_bytes("Введи вектор a напрямую:")

    use_mapping_for_b2 = input_yes_no("Собрать второй рабочий вектор из b по таблице?")
    if use_mapping_for_b2:
        b2_mapping = input_mapping("c")
        b2 = build_from_mapping(b_source, b2_mapping, "c")
    else:
        b2 = input_16_bytes("Введи второй рабочий вектор напрямую:")

    k = input_16_bytes("Введи ключ k (16 байтов):")

    title("ИТОГОВЫЕ ВХОДНЫЕ ВЕКТОРЫ")
    show_vector("Исходный b0..b15", b_source)
    show_vector("Рабочий вектор a", a)
    show_vector("Второй рабочий вектор", b2)
    show_vector("Ключ k", k)

    title("ОСНОВНЫЕ ПРЕОБРАЗОВАНИЯ")
    x = X_verbose(k, a)
    s = S_verbose(a)
    s_inv = S_inv_verbose(a)
    r = R_verbose(a)
    r_inv = R_inv_verbose(a)
    l = L_verbose(a)
    l_inv = L_inv_verbose(a)
    f1, f2 = F_verbose(k, a, b2)

    title("ПРОВЕРКИ ОБРАТИМОСТИ")
    check_equal("S^-1(S(a)) = a", a, S_inv_verbose(S_verbose(a)))
    check_equal("R^-1(R(a)) = a", a, R_inv_verbose(R_verbose(a)))
    check_equal("L^-1(L(a)) = a", a, L_inv_verbose(L_verbose(a)))

    title("ФИНАЛЬНАЯ СВОДКА")
    df = pd.DataFrame([
        {"Преобразование": "X[k](a)", "HEX": bytes_hex_str(x), "BIN": bytes_bin_str(x)},
        {"Преобразование": "S(a)", "HEX": bytes_hex_str(s), "BIN": bytes_bin_str(s)},
        {"Преобразование": "S^-1(a)", "HEX": bytes_hex_str(s_inv), "BIN": bytes_bin_str(s_inv)},
        {"Преобразование": "R(a)", "HEX": bytes_hex_str(r), "BIN": bytes_bin_str(r)},
        {"Преобразование": "R^-1(a)", "HEX": bytes_hex_str(r_inv), "BIN": bytes_bin_str(r_inv)},
        {"Преобразование": "L(a)", "HEX": bytes_hex_str(l), "BIN": bytes_bin_str(l)},
        {"Преобразование": "L^-1(a)", "HEX": bytes_hex_str(l_inv), "BIN": bytes_bin_str(l_inv)},
        {"Преобразование": "F first", "HEX": bytes_hex_str(f1), "BIN": bytes_bin_str(f1)},
        {"Преобразование": "F second", "HEX": bytes_hex_str(f2), "BIN": bytes_bin_str(f2)},
    ])
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()