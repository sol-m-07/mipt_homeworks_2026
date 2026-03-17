#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Неизвестная команда!"
NONPOSITIVE_VALUE_MSG = "Значение должно быть больше нуля!"
INCORRECT_DATE_MSG = "Неправильная дата!"
OP_SUCCESS_MSG = "Добавлено"

DATE_SIZE = 3
INCOME_SIZE = 2
EXPENSE_SIZE = 3
NUMBER_OF_MONTHS = 12

DAY_LEN = 2
MONTH_LEN = 2

FEBRUARY = 2
DAYS_IN_LEAP_FEBRUARY = 29
DAYS_IN_MONTH = (
    0,
    31,
    28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
)

IncomeHistory = list[tuple[float, int, int, int]]
ExpenseHistory = list[tuple[str, float, int, int, int]]


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def earlier(date1: tuple[int, int, int], date2: tuple[int, int, int]) -> bool:
    first = (date1[2], date1[1], date1[0])
    second = (date2[2], date2[1], date2[0])
    return first <= second


def date_is_valid(date: list[str]) -> bool:
    day_str = date[0]
    month_str = date[1]
    is_day_len_valid = len(day_str) == DAY_LEN
    is_month_len_valid = len(month_str) == MONTH_LEN
    return is_day_len_valid and is_month_len_valid


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    split_dt = maybe_dt.split("-")
    if (
        len(split_dt) != DATE_SIZE
        or not date_is_valid(split_dt)
        or not split_dt[2].isdigit()
    ):
        return None

    day, month, year = map(int, split_dt)
    if not (1 <= month <= NUMBER_OF_MONTHS):
        return None

    days_in_month = DAYS_IN_MONTH[month]
    if month == FEBRUARY and is_leap_year(year):
        days_in_month = DAYS_IN_LEAP_FEBRUARY

    if not (1 <= day <= days_in_month):
        return None
    return day, month, year


def extract_sum(maybe_sum: str) -> float | None:
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


def extract_category(maybe_category: str) -> bool:
    category = maybe_category.split()
    if len(category) != 1:
        return False
    name = category[0]
    return not ("." in name or "," in name)


def iter_input_lines() -> list[str]:
    with open(0) as stdin:
        return stdin.readlines()


def income_processing(command: list[str], incomes: IncomeHistory) -> None:
    if len(command) != INCOME_SIZE:
        print(UNKNOWN_COMMAND_MSG)
        return

    value = extract_sum(command[0])
    date = extract_date(command[1])

    if value is None:
        print(UNKNOWN_COMMAND_MSG)
        return

    if value <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return

    if date is None:
        print(INCORRECT_DATE_MSG)
        return

    day, month, year = date
    incomes.append((value, day, month, year))

    print(OP_SUCCESS_MSG)


def expense_processing(command: list[str], expenses: ExpenseHistory) -> None:
    if len(command) != EXPENSE_SIZE or not extract_category(command[0]):
        print(UNKNOWN_COMMAND_MSG)
        return

    value = extract_sum(command[1])
    date = extract_date(command[2])

    if value is None:
        print(UNKNOWN_COMMAND_MSG)
        return

    if value <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return

    if date is None:
        print(INCORRECT_DATE_MSG)
        return

    day, month, year = date
    expenses.append((command[0], value, day, month, year))

    print(OP_SUCCESS_MSG)


def _calculate_total_capital(
    incomes: IncomeHistory,
    expenses: ExpenseHistory,
    date: tuple[int, int, int],
) -> float:
    incomes_before_date = [item for item in incomes if earlier(item[1:], date)]
    expenses_before_date = [item for item in expenses if earlier(item[2:], date)]
    income_sum = sum(item[0] for item in incomes_before_date)
    expense_sum = sum(item[1] for item in expenses_before_date)
    return income_sum - expense_sum


def _is_same_month(
    record_month: int,
    record_year: int,
    date: tuple[int, int, int],
) -> bool:
    month = date[1]
    year = date[2]
    return record_month == month and record_year == year


def _get_month_income(
    incomes: IncomeHistory,
    date: tuple[int, int, int],
) -> float:
    incomes_before_date = [item for item in incomes if earlier(item[1:], date)]
    return sum(
        item[0]
        for item in incomes_before_date
        if _is_same_month(item[2], item[3], date)
    )


def _get_month_expenses(
    expenses: ExpenseHistory,
    date: tuple[int, int, int],
) -> tuple[list[tuple[str, float, int, int, int]], float]:
    expenses_before_date = [item for item in expenses if earlier(item[2:], date)]
    month_expenses = [
        item
        for item in expenses_before_date
        if _is_same_month(item[3], item[4], date)
    ]
    total_month_expense = sum(item[1] for item in month_expenses)
    return month_expenses, total_month_expense


def _print_month_result(month_income: float, month_expense: float) -> None:
    if month_income >= month_expense:
        print(
            "В этом месяце прибыль составила "  # noqa: RUF001
            f"{month_income - month_expense:.2f} рублей",
        )
    else:
        print(
            "В этом месяце убыток составил "  # noqa: RUF001
            f"{month_expense - month_income:.2f} рублей",
        )

    print(f"Доходы: {month_income:.2f} рублей")
    print(f"Расходы: {month_expense:.2f} рублей")


def _print_expense_details(
    list_month_expense: list[tuple[str, float, int, int, int]],
) -> None:
    print()
    print("Детализация (категория: сумма):")

    if not list_month_expense:
        return

    list_month_expense.sort()
    current_category = list_month_expense[0][1]
    category_number = 1

    for index, expense in enumerate(list_month_expense[1:], start=1):
        previous_expense = list_month_expense[index - 1]
        if expense[0] == previous_expense[0]:
            current_category += expense[1]
            continue

        print(f"{category_number}. {previous_expense[0]}: {round(current_category)}")
        current_category = expense[1]
        category_number += 1

    last_category = list_month_expense[-1][0]
    print(f"{category_number}. {last_category}: {round(current_category)}")


def stats_processing(command: list[str], incomes: IncomeHistory, expenses: ExpenseHistory) -> None:
    if len(command) != 1:
        print(UNKNOWN_COMMAND_MSG)
        return

    date = extract_date(command[0])
    if date is None:
        print(INCORRECT_DATE_MSG)
        return

    print(f"Ваша статистика по состоянию на {command[0]}:")
    total_capital = _calculate_total_capital(incomes, expenses, date)
    print(f"Суммарный капитал: {total_capital:.2f} рублей")

    month_income = _get_month_income(incomes, date)
    list_month_expense, month_expense = _get_month_expenses(expenses, date)
    _print_month_result(month_income, month_expense)
    _print_expense_details(list_month_expense)


def process_line(line: str, incomes: IncomeHistory, expenses: ExpenseHistory) -> None:
    command = line.split()
    if not command:
        print(UNKNOWN_COMMAND_MSG)
        return

    command_name = command[0]
    if command_name == "income":
        income_processing(command[1:], incomes)
        return

    if command_name == "cost":
        expense_processing(command[1:], expenses)
        return

    if command_name == "stats":
        stats_processing(command[1:], incomes, expenses)
        return

    print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    incomes: IncomeHistory = []
    expenses: ExpenseHistory = []

    while True:
        line = input()
        if not line:
            break
        process_line(line, incomes, expenses)


if __name__ == "__main__":
    main()
