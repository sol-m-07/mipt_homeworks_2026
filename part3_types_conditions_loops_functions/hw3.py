#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

CATEGORY_SEP = "::"
_FIRST_HALF_MDAYS = (31, 28, 31, 30, 31, 30)
_SECOND_HALF_MDAYS = (31, 31, 30, 31, 30, 31)
_MONTH_DAYS = _FIRST_HALF_MDAYS + _SECOND_HALF_MDAYS

_AGG_INCOME_TOTAL = "ti"
_AGG_EXPENSE_TOTAL = "te"
_AGG_INCOME_MONTH = "mi"
_AGG_EXPENSE_MONTH = "me"
_AGG_DETAILS = "details"

_FEBRUARY_MONTH = 2
_FLOAT_ZERO = float(_FEBRUARY_MONTH - _FEBRUARY_MONTH)
_MONTHS_PER_YEAR = 12
_DATE_PARTS_COUNT = 3
_DATE_TUPLE_LEN = 3
_THOUSAND_GROUP_WIDTH = 3
_INCOME_CMD_WORDS = 3
_COST_CATEGORIES_WORDS = 2
_COST_PURCHASE_MIN_WORDS = 4
_STATS_CMD_WORDS = 2

type _StatsBodyBundle = tuple[float, str, float, float, float, dict[str, float]]


EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


financial_transactions_storage: list[dict[str, object]] = []


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def _days_in_month(month: int, year: int) -> int:
    days = _MONTH_DAYS[month - 1]
    if month == _FEBRUARY_MONTH and is_leap_year(year):
        return 29
    return days


def _validated_ymd(day_s: str, month_s: str, year_s: str) -> tuple[int, int, int] | None:
    if not day_s or not month_s or not year_s:
        return None
    if not day_s.isdigit() or not month_s.isdigit() or not year_s.isdigit():
        return None
    day = int(day_s)
    month = int(month_s)
    year = int(year_s)
    if month < 1 or month > _MONTHS_PER_YEAR:
        return None
    dim = _days_in_month(month, year)
    if day < 1 or day > dim:
        return None
    return (day, month, year)


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: tuple формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    chunks = maybe_dt.split("-")
    if len(chunks) != _DATE_PARTS_COUNT:
        return None
    return _validated_ymd(chunks[0], chunks[1], chunks[2])


def _date_to_ymd(dmy: tuple[int, int, int]) -> tuple[int, int, int]:
    day, month, year = dmy
    return (year, month, day)


def _tuple_dmy_to_ymd(raw: tuple[object, object, object]) -> tuple[int, int, int]:
    d = int(raw[0])
    m = int(raw[1])
    y = int(raw[2])
    return (y, m, d)


def _record_ymd(record: dict[str, object]) -> tuple[int, int, int] | None:
    if not record:
        return None
    raw = record["date"]
    if isinstance(raw, tuple) and len(raw) == _DATE_TUPLE_LEN:
        triple = (raw[0], raw[1], raw[2])
        return _tuple_dmy_to_ymd(triple)
    if isinstance(raw, str):
        parsed = extract_date(raw)
        if parsed is None:
            return None
        return _date_to_ymd(parsed)
    return None


def _digits_only(s: str) -> bool:
    return bool(s) and all(ch.isdigit() for ch in s)


def _split_decimal_parts(normalized: str) -> tuple[str, str] | None:
    if normalized == "":
        return None
    if normalized.count(".") > 1:
        return None
    if "." in normalized:
        whole, frac = normalized.split(".", 1)
    else:
        whole = normalized
        frac = ""
    return (whole, frac)


def _decimal_from_parts(whole: str, frac: str) -> float | None:
    whole_ok = whole == "" or _digits_only(whole)
    frac_ok = frac == "" or _digits_only(frac)
    if not whole_ok or not frac_ok:
        return None
    if whole == "" and frac == "":
        return None
    if whole == "":
        return int(frac) / (10 ** len(frac))
    if frac == "":
        return float(int(whole))
    whole_val = float(int(whole))
    frac_len = len(frac)
    frac_val = int(frac) / (10**frac_len)
    return whole_val + frac_val


def parse_decimal_string(token: str) -> float | None:
    normalized = token.strip().replace(",", ".")
    parts = _split_decimal_parts(normalized)
    if parts is None:
        return None
    whole, frac = parts
    return _decimal_from_parts(whole, frac)


def _category_valid(category_name: str) -> bool:
    if CATEGORY_SEP not in category_name:
        return False
    common, target = category_name.split(CATEGORY_SEP, 1)
    if common == "" or target == "":
        return False
    if common not in EXPENSE_CATEGORIES:
        return False
    return target in EXPENSE_CATEGORIES[common]


def _split_camel_target(target: str) -> list[str]:
    words: list[str] = []
    buf = ""
    for ch in target:
        if ch.isupper() and buf and buf[-1].islower():
            words.append(buf)
            buf = ch
        else:
            buf += ch
    if buf:
        words.append(buf)
    return words


def _title_from_words(words: list[str], fallback: str) -> str:
    if not words:
        return fallback
    first = words[0]
    if len(first) > 1:  # noqa: SIM108
        head = first[0].upper() + first[1:].lower()
    else:
        head = first.upper()
    if len(words) == 1:
        return head
    tail = " ".join(w.lower() for w in words[1:])
    return f"{head} {tail}"


def expense_display_name(category_full: str) -> str:
    if CATEGORY_SEP in category_full:  # noqa: SIM108
        target = category_full.split(CATEGORY_SEP, 1)[1]
    else:
        target = category_full
    if " " in target:
        return target[0].upper() + target[1:] if target else target
    return _title_from_words(_split_camel_target(target), target)


def _format_stat_money(value: float) -> str:
    return f"{value:.2f}"


def _format_detail_amount(value: float) -> str:
    rounded = round(value, 2)
    if rounded.is_integer():
        n = int(rounded)
        sign = "-" if n < 0 else ""
        n_abs = abs(n)
        s = str(n_abs)
        if len(s) <= _THOUSAND_GROUP_WIDTH:
            return sign + s
        groups: list[str] = []
        while s:
            groups.append(s[-3:])
            s = s[:-3]
        return sign + ",".join(reversed(groups))
    return _format_stat_money(rounded)


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    parsed = extract_date(income_date)
    if parsed is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({"amount": amount, "date": parsed})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    parsed = extract_date(income_date)
    if parsed is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    if not _category_valid(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append({"category": category_name, "amount": amount, "date": parsed})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    pairs = (f"{key}::{value}" for key, values in EXPENSE_CATEGORIES.items() for value in values)
    return "\n".join(pairs)


def _new_agg() -> dict[str, float | dict[str, float]]:
    return {
        _AGG_INCOME_TOTAL: _FLOAT_ZERO,
        _AGG_EXPENSE_TOTAL: _FLOAT_ZERO,
        _AGG_INCOME_MONTH: _FLOAT_ZERO,
        _AGG_EXPENSE_MONTH: _FLOAT_ZERO,
        _AGG_DETAILS: {},
    }


def _process_record_for_agg(
    rec: dict[str, object],
    report_key: tuple[int, int, int],
    ry: int,
    rm: int,
    agg: dict[str, float | dict[str, float]],
) -> None:
    ymd = _record_ymd(rec)
    if ymd is None or ymd >= report_key:
        return
    amount = float(rec["amount"])
    is_expense = "category" in rec
    if is_expense:
        agg[_AGG_EXPENSE_TOTAL] += amount
    else:
        agg[_AGG_INCOME_TOTAL] += amount
    y, m, _ = ymd
    if y != ry or m != rm:
        return
    if is_expense:
        agg[_AGG_EXPENSE_MONTH] += amount
        label = expense_display_name(str(rec["category"]))
        details = agg[_AGG_DETAILS]
        details[label] = details.get(label, _FLOAT_ZERO) + amount
    else:
        agg[_AGG_INCOME_MONTH] += amount


def _aggregate_stats(
    storage: list[dict[str, object]],
    report_key: tuple[int, int, int],
) -> dict[str, float | dict[str, float]]:
    agg = _new_agg()
    ry, rm, _ = report_key
    for rec in storage:
        _process_record_for_agg(rec, report_key, ry, rm, agg)
    return agg


def _monthly_flow(month_income: float, month_expense: float) -> tuple[str, float]:
    income_r = round(month_income, 2)
    expense_r = round(month_expense, 2)
    if income_r >= expense_r:
        return "profit", round(income_r - expense_r, 2)
    return "loss", round(expense_r - income_r, 2)


class _StatsBody:
    __slots__ = ("capital", "details", "flow_amount", "flow_word", "month_expense", "month_income")

    def __init__(self, bundle: _StatsBodyBundle) -> None:
        self.capital = bundle[0]
        self.flow_word = bundle[1]
        self.flow_amount = bundle[2]
        self.month_income = bundle[3]
        self.month_expense = bundle[4]
        self.details = bundle[5]


def _detail_sort_key(item: tuple[str, float]) -> str:
    return item[0].casefold()


def _build_stats_lines(report_date: str, body: _StatsBody) -> list[str]:
    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {_format_stat_money(body.capital)} rubles",
        f"This month, the {body.flow_word} amounted to {_format_stat_money(body.flow_amount)} rubles.",
        f"Income: {_format_stat_money(body.month_income)} rubles",
        f"Expenses: {_format_stat_money(body.month_expense)} rubles",
        "",
        "Details (category: amount):",
    ]
    details = body.details
    if details:
        ordered = sorted(details.items(), key=_detail_sort_key)
        for idx, (label, amt) in enumerate(ordered, start=1):
            lines.append(f"{idx}. {label}: {_format_detail_amount(amt)}")
    return lines


def stats_handler(report_date: str) -> str:
    report_dmy = extract_date(report_date)
    if report_dmy is None:
        return INCORRECT_DATE_MSG
    report_key = _date_to_ymd(report_dmy)
    agg = _aggregate_stats(financial_transactions_storage, report_key)
    capital = round(agg[_AGG_INCOME_TOTAL] - agg[_AGG_EXPENSE_TOTAL], 2)
    flow_word, flow_amt = _monthly_flow(agg[_AGG_INCOME_MONTH], agg[_AGG_EXPENSE_MONTH])
    body = _StatsBody(
        (
            capital,
            flow_word,
            flow_amt,
            round(agg[_AGG_INCOME_MONTH], 2),
            round(agg[_AGG_EXPENSE_MONTH], 2),
            agg[_AGG_DETAILS],
        ),
    )
    return "\n".join(_build_stats_lines(report_date, body))


def _handle_income_command(parts: list[str]) -> str:
    if len(parts) != _INCOME_CMD_WORDS:
        return UNKNOWN_COMMAND_MSG
    amount_raw = parse_decimal_string(parts[1])
    if amount_raw is None:
        return UNKNOWN_COMMAND_MSG
    if amount_raw <= 0:
        return NONPOSITIVE_VALUE_MSG
    if extract_date(parts[2]) is None:
        return INCORRECT_DATE_MSG
    return income_handler(amount_raw, parts[2])


def _cost_after_validated_parse(category_name: str, amount_raw: float, date_token: str) -> str:
    msg = cost_handler(category_name, amount_raw, date_token)
    if msg == NOT_EXISTS_CATEGORY:
        return f"{msg}\n{cost_categories_handler()}"
    return msg


def _handle_cost_purchase(parts: list[str]) -> str:
    date_token = parts[-1]
    amount_token = parts[-2]
    category_name = " ".join(parts[1:-2])
    amount_raw = parse_decimal_string(amount_token)
    if amount_raw is None:
        return UNKNOWN_COMMAND_MSG
    if amount_raw <= 0:
        return NONPOSITIVE_VALUE_MSG
    if extract_date(date_token) is None:
        return INCORRECT_DATE_MSG
    return _cost_after_validated_parse(category_name, amount_raw, date_token)


def _handle_cost_command(parts: list[str]) -> str:
    if len(parts) == _COST_CATEGORIES_WORDS and parts[1] == "categories":
        return cost_categories_handler()
    if len(parts) < _COST_PURCHASE_MIN_WORDS:
        return UNKNOWN_COMMAND_MSG
    return _handle_cost_purchase(parts)


def _handle_stats_command(parts: list[str]) -> str:
    if len(parts) != _STATS_CMD_WORDS:
        return UNKNOWN_COMMAND_MSG
    return stats_handler(parts[1])


def main() -> None:
    """Ваш код здесь"""
    handlers = {
        "income": _handle_income_command,
        "cost": _handle_cost_command,
        "stats": _handle_stats_command,
    }

    for _ in iter(int, 1):
        stripped = input().strip()
        if stripped == "":
            continue
        parts = stripped.split()
        cmd = parts[0]
        handler = handlers.get(cmd)
        if handler is None:
            print(UNKNOWN_COMMAND_MSG)
        else:
            print(handler(parts))


if __name__ == "__main__":
    main()
