#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

DATE_SIZE = 3
INCOME_CMD_SIZE = 2
EXPENSE_CMD_SIZE = 3
NUMBER_OF_MONTHS = 12
DAY_LEN = 2
MONTH_LEN = 2
FEBRUARY = 2
DAYS_IN_LEAP_FEBRUARY = 29
CATEGORY_SEPARATOR = "::"

DAYS_IN_MONTH = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

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


def _date_format_is_valid(parts: list[str]) -> bool:
    return (
        len(parts[0]) == DAY_LEN
        and parts[0].isdigit()
        and len(parts[1]) == MONTH_LEN
        and parts[1].isdigit()
        and parts[2].isdigit()
    )


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parts = maybe_dt.split("-")
    if len(parts) != DATE_SIZE or not _date_format_is_valid(parts):
        return None

    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
    if not (1 <= month <= NUMBER_OF_MONTHS):
        return None

    days_in_month = DAYS_IN_MONTH[month]
    if month == FEBRUARY and is_leap_year(year):
        days_in_month = DAYS_IN_LEAP_FEBRUARY

    if not (1 <= day <= days_in_month):
        return None
    return day, month, year


def _is_valid_category(category_name: str) -> bool:
    parts = category_name.split(CATEGORY_SEPARATOR)
    if len(parts) != 2:  # noqa: PLR2004
        return False
    common, target = parts
    return common in EXPENSE_CATEGORIES and target in EXPENSE_CATEGORIES[common]


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(income_date)
    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({"amount": amount, "date": date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if not _is_valid_category(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(income_date)
    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {"category": category_name, "amount": amount, "date": date},
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(
        f"{k}::{v}" for k, kv in EXPENSE_CATEGORIES.items() for v in kv
    )


def _earlier(
    date1: tuple[int, int, int],
    date2: tuple[int, int, int],
) -> bool:
    return (date1[2], date1[1], date1[0]) <= (date2[2], date2[1], date2[0])


def _is_same_month(
    t_date: tuple[int, int, int],
    target_date: tuple[int, int, int],
) -> bool:
    return t_date[1] == target_date[1] and t_date[2] == target_date[2]


def stats_handler(report_date: str) -> str:
    date = extract_date(report_date)
    if date is None:
        return INCORRECT_DATE_MSG

    total_income = 0.0
    total_expense = 0.0
    month_income = 0.0
    month_expense = 0.0
    expenses_by_category: dict[str, float] = {}

    for transaction in financial_transactions_storage:
        if not transaction:
            continue
        t_date = transaction["date"]
        if not _earlier(t_date, date):
            continue

        amount = transaction["amount"]
        same_month = _is_same_month(t_date, date)

        if "category" in transaction:
            total_expense += amount
            if same_month:
                month_expense += amount
                cat = transaction["category"]
                expenses_by_category[cat] = (
                    expenses_by_category.get(cat, 0) + amount
                )
        else:
            total_income += amount
            if same_month:
                month_income += amount

    total_capital = total_income - total_expense

    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total_capital:.2f} rubles",
    ]

    if month_income >= month_expense:
        diff = month_income - month_expense
        lines.append(
            f"This month, the profit amounted to {diff:.2f} rubles",
        )
    else:
        diff = month_expense - month_income
        lines.append(
            f"This month, the loss amounted to {diff:.2f} rubles",
        )

    lines.append(f"Income: {month_income:.2f} rubles")
    lines.append(f"Expenses: {month_expense:.2f} rubles")
    lines.append("")
    lines.append("Details (category: amount):")

    if expenses_by_category:
        number = 1
        for cat, total in sorted(expenses_by_category.items()):
            lines.append(f"{number}. {cat}: {round(total)}")
            number += 1

    return "\n".join(lines)


def _extract_sum(maybe_sum: str) -> float | None:
    if not maybe_sum:
        return None
    normalized = maybe_sum.replace(",", ".")
    if normalized[0] == "." or normalized.count(".") > 1:
        return None
    digits_part = normalized[1:] if normalized[0] == "-" else normalized
    if not digits_part:
        return None
    for char in digits_part:
        if not (char.isdigit() or char == "."):
            return None
    return float(normalized)


def _process_income(args: list[str]) -> None:
    if len(args) != INCOME_CMD_SIZE:
        print(UNKNOWN_COMMAND_MSG)
        return
    amount = _extract_sum(args[0])
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return
    print(income_handler(amount, args[1]))


def _process_cost(args: list[str]) -> None:
    if args and args[0] == "categories":
        print(cost_categories_handler())
        return
    if len(args) != EXPENSE_CMD_SIZE:
        print(UNKNOWN_COMMAND_MSG)
        return
    amount = _extract_sum(args[1])
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return
    result = cost_handler(args[0], amount, args[2])
    print(result)
    if result == NOT_EXISTS_CATEGORY:
        print(cost_categories_handler())


def _process_stats(args: list[str]) -> None:
    if len(args) != 1:
        print(UNKNOWN_COMMAND_MSG)
        return
    print(stats_handler(args[0]))


def _process_line(line: str) -> None:
    parts = line.split()
    if not parts:
        print(UNKNOWN_COMMAND_MSG)
        return

    command = parts[0]
    args = parts[1:]

    if command == "income":
        _process_income(args)
    elif command == "cost":
        _process_cost(args)
    elif command == "stats":
        _process_stats(args)
    else:
        print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    while True:
        line = input()
        if not line:
            break
        _process_line(line)


if __name__ == "__main__":
    main()
