import argparse
from typing import List, Dict, Any
import pandas as pd
from .views import home_view
from .services import analyze_cashback_categories
from .reports import spending_by_category
from .utils import load_transactions


def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description="Анализатор транзакций")
    subparsers = parser.add_subparsers(dest="command")

    # Home command
    home_parser = subparsers.add_parser("home", help="Генерация данных главной страницы")
    home_parser.add_argument("date", type=str, help="Дата в формате YYYY-MM-DD HH:MM:SS")

    # Cashback command
    cashback_parser = subparsers.add_parser("cashback", help="Анализ выгодных категорий")
    cashback_parser.add_argument("year", type=int, help="Год для анализа")
    cashback_parser.add_argument("month", type=int, help="Месяц для анализа (1-12)")

    # Report command
    report_parser = subparsers.add_parser("report", help="Генерация отчета по категории")
    report_parser.add_argument("category", type=str, help="Категория для анализа")
    report_parser.add_argument("-d", "--date", type=str, help="Дата в формате YYYY-MM-DD")

    return parser.parse_args()


def process_home_command(args: argparse.Namespace) -> None:
    """Обработка команды home"""
    try:
        result = home_view(args.date)
        print(result)
    except Exception as e:
        print(f"Ошибка генерации главной страницы: {str(e)}")


def process_cashback_command(args: argparse.Namespace) -> None:
    """Обработка команды cashback"""
    try:
        transactions: List[Dict[str, Any]] = load_transactions()
        result = analyze_cashback_categories(transactions, args.year, args.month)
        print(result)
    except Exception as e:
        print(f"Ошибка анализа кешбэка: {str(e)}")


def process_report_command(args: argparse.Namespace) -> None:
    """Обработка команды report"""
    try:
        transactions_data: List[Dict[str, Any]] = load_transactions()
        df = pd.DataFrame(transactions_data)
        result = spending_by_category(df, args.category, args.date)
        print(result.to_string(index=False))
    except Exception as e:
        print(f"Ошибка генерации отчета: {str(e)}")


def main() -> None:
    """Главная функция для запуска приложения"""
    args = parse_args()

    command_handlers = {
        "home": process_home_command,
        "cashback": process_cashback_command,
        "report": process_report_command
    }
    if args.command in command_handlers:
        command_handlers[args.command](args)
    else:
        print("Неизвестная команда. Используйте --help для списка команд")


if __name__ == "__main__":
    main()
