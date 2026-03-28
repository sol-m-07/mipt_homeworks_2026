#!/usr/bin/env python

from typing import Any

DateTuple = tuple[int, int, int]
ExpenseTotals = tuple[dict[str, float], float]

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

DATE_SIZE = 3
INCOME_SIZE = 2
EXPENSE_SIZE = 3
CATEGORY_SIZE = 2
NUMBER_OF_MONTHS = 12

DAY_LEN = 2
MONTH_LEN = 2
YEAR_LEN = 4

FEBRUARY = 2
DAYS_IN_LEAP_FEBRUARY = 29
NUMBERS_OF_DAYS = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 30,
    9: 31,
    10: 31,
    11: 30,
    12: 31,
}

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


financial_transactions_storage: list[dict[str, Any]] = []

KEY_AMOUNT = "amount"
KEY_CATEGORY = "category"
KEY_DATE = "date"


def _record_failed_transaction() -> None:
    financial_transactions_storage.append({})


def _decimal_body_ok(body: str) -> bool:
    return all(c.isdigit() or c == "." for c in body)


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def date_is_valid(date: list[str]) -> bool:
    if len(date) != DATE_SIZE:
        return False
    day = date[0]
    month = date[1]
    year = date[2]
    if len(day) != DAY_LEN or not day.isdigit():
        return False
    if len(month) != MONTH_LEN or not month.isdigit():
        return False
    return len(year) == YEAR_LEN and year.isdigit()


def extract_date(maybe_dt: str) -> DateTuple | None:
    split_dt = maybe_dt.split("-")
    if not date_is_valid(split_dt):
        return None
    day = int(split_dt[0])
    month = int(split_dt[1])
    year = int(split_dt[2])
    if not (1 <= month <= NUMBER_OF_MONTHS):
        return None
    max_day = DAYS_IN_LEAP_FEBRUARY if month == FEBRUARY and is_leap_year(year) else NUMBERS_OF_DAYS[month]
    if day < 1 or day > max_day:
        return None
    return day, month, year


def extract_sum(maybe_sum: str) -> float | None:
    if maybe_sum == "":
        return None

    maybe_sum = maybe_sum.replace(",", ".")

    if maybe_sum[0] == "." or maybe_sum.count(".") > 1:
        return None

    body = maybe_sum[1:] if maybe_sum[0] == "-" else maybe_sum
    if not _decimal_body_ok(body):
        return None
    return float(maybe_sum)


def _extract_sum_for_command(token: str) -> float | None:
    amount = extract_sum(token)
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
    return amount


def _normalize_storage_date(raw: Any) -> DateTuple | None:
    if isinstance(raw, tuple) and len(raw) == DATE_SIZE:
        d, m, y = raw
        if isinstance(d, int) and isinstance(m, int) and isinstance(y, int):
            return d, m, y
    if isinstance(raw, str):
        return extract_date(raw)
    return None


def _date_not_after(transaction: DateTuple, report: DateTuple) -> bool:
    t_key = (transaction[2], transaction[1], transaction[0])
    r_key = (report[2], report[1], report[0])
    return t_key <= r_key


def _is_known_expense_category(category_name: str) -> bool:
    parts = category_name.split("::")
    if len(parts) != CATEGORY_SIZE:
        return False
    if not parts[0] or not parts[1]:
        return False
    common, target = parts[0], parts[1]
    for segment in (common, target):
        if "." in segment or "," in segment:
            return False
    return common in EXPENSE_CATEGORIES and target in EXPENSE_CATEGORIES[common]


def _is_same_month(transaction: DateTuple, report: DateTuple) -> bool:
    same_month = transaction[1] == report[1]
    same_year = transaction[2] == report[2]
    return same_month and same_year


def _parsed_date_for_iteration(
    transaction: dict[str, Any],
    report: DateTuple,
    *,
    same_month_only: bool,
) -> DateTuple | None:
    if not transaction:
        return None
    parsed_date = _normalize_storage_date(transaction.get(KEY_DATE))
    if parsed_date is None:
        return None
    if not _date_not_after(parsed_date, report):
        return None
    if same_month_only and not _is_same_month(parsed_date, report):
        return None
    return parsed_date


def _iter_transactions_upto(
    report: DateTuple,
    *,
    same_month_only: bool,
) -> Any:
    for transaction in financial_transactions_storage:
        parsed_date = _parsed_date_for_iteration(
            transaction,
            report,
            same_month_only=same_month_only,
        )
        if parsed_date is None:
            continue
        yield transaction, parsed_date


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        _record_failed_transaction()
        return NONPOSITIVE_VALUE_MSG
    parsed = extract_date(income_date)
    if parsed is None:
        _record_failed_transaction()
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({KEY_AMOUNT: amount, KEY_DATE: parsed})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        _record_failed_transaction()
        return NONPOSITIVE_VALUE_MSG
    parsed = extract_date(income_date)
    if parsed is None:
        _record_failed_transaction()
        return INCORRECT_DATE_MSG
    if not _is_known_expense_category(category_name):
        _record_failed_transaction()
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append(
        {KEY_CATEGORY: category_name, KEY_AMOUNT: amount, KEY_DATE: parsed},
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines: list[str] = []
    for common, targets in EXPENSE_CATEGORIES.items():
        for target in targets:
            lines.append(f"{common}::{target}")  # noqa: PERF401
    return "\n".join(lines)


def _calculate_total_capital(report: DateTuple) -> float:
    total_income: float = 0
    total_expense: float = 0
    for transaction, _ in _iter_transactions_upto(report, same_month_only=False):
        amt = float(transaction[KEY_AMOUNT])
        if KEY_CATEGORY in transaction:
            total_expense += amt
        else:
            total_income += amt
    return round(total_income - total_expense, 2)


def _get_month_income(report: DateTuple) -> float:
    total: float = 0
    for transaction, _ in _iter_transactions_upto(report, same_month_only=True):
        if KEY_CATEGORY in transaction:
            continue
        total += float(transaction[KEY_AMOUNT])
    return round(total, 2)


def _get_month_expenses(report: DateTuple) -> ExpenseTotals:
    by_category: dict[str, float] = {}
    total: float = 0
    for transaction, _ in _iter_transactions_upto(report, same_month_only=True):
        if KEY_CATEGORY not in transaction:
            continue
        amt = float(transaction[KEY_AMOUNT])
        total += amt
        cat = transaction[KEY_CATEGORY]
        prev_val = by_category.get(cat)
        if prev_val is None:
            by_category[cat] = amt
        else:
            by_category[cat] = prev_val + amt
    return by_category, round(total, 2)


def _format_detail_amount(amount: float) -> str:
    if amount == int(amount):
        return str(int(amount))
    return f"{amount:.2f}"


def _print_month_result(month_income: float, month_expense: float) -> str:
    net = month_income - month_expense
    if net >= 0:
        return f"This month, the profit amounted to {net:.2f} rubles."
    loss_rub = -net
    template = "This month, the loss amounted to {loss:.2f} rubles."
    return template.format(loss=loss_rub)


def _expense_category_sort_key(pair: tuple[str, float]) -> str:
    return pair[0]


def _print_expense_details(expenses_by_category: dict[str, float]) -> str:
    if not expenses_by_category:
        return ""
    lines: list[str] = []
    index = 1
    pairs = sorted(expenses_by_category.items(), key=_expense_category_sort_key)
    for name, amt in pairs:
        lines.append(f"{index}. {name}: {_format_detail_amount(amt)}")
        index += 1
    return "\n".join(lines)


def stats_handler(report_date: str, report: DateTuple | None = None) -> str:
    parsed = extract_date(report_date) if report is None else report
    if parsed is None:
        return ""

    total_capital = _calculate_total_capital(parsed)
    month_income = _get_month_income(parsed)
    expenses_map, month_expense = _get_month_expenses(parsed)
    month_line = _print_month_result(month_income, month_expense)
    details = _print_expense_details(expenses_map)

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total_capital:.2f} rubles",
        month_line,
        f"Income: {month_income:.2f} rubles",
        f"Expenses: {month_expense:.2f} rubles",
        "",
        "Details (category: amount):",
    ]
    if details:
        lines.append(details)
    return "\n".join(lines)


def income_processing(command: list[str]) -> None:
    if len(command) != INCOME_SIZE:
        print(UNKNOWN_COMMAND_MSG)
        return
    amount = _extract_sum_for_command(command[0])
    if amount is None:
        return
    print(income_handler(amount, command[1]))


def expense_processing(command: list[str]) -> None:
    if len(command) == 1 and command[0] == "categories":
        print(cost_categories_handler())
        return
    if len(command) != EXPENSE_SIZE:
        print(UNKNOWN_COMMAND_MSG)
        return
    category_name = command[0]
    amount = _extract_sum_for_command(command[1])
    if amount is None:
        return
    msg = cost_handler(category_name, amount, command[2])
    print(msg)
    if msg == NOT_EXISTS_CATEGORY:
        print(cost_categories_handler())


def stats_processing(command: list[str]) -> None:
    if len(command) != 1:
        print(UNKNOWN_COMMAND_MSG)
        return

    parsed = extract_date(command[0])
    if parsed is None:
        print(INCORRECT_DATE_MSG)
        return

    print(stats_handler(command[0], parsed))


def process_line(line: str) -> None:
    command = line.split()
    if not command:
        print(UNKNOWN_COMMAND_MSG)
        return

    command_name = command[0]
    if command_name == "income":
        income_processing(command[1:])
        return

    if command_name == "cost":
        expense_processing(command[1:])
        return

    if command_name == "stats":
        stats_processing(command[1:])
        return

    print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    while True:
        line = input()
        if not line:
            break
        process_line(line)


if __name__ == "__main__":
    main()
