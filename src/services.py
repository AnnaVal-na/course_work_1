import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from functools import reduce

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


def analyze_cashback_categories(
        data: List[Dict[str, Any]],
        year: int,
        month: int
) -> str:
    """
    Анализирует выгодность категорий для повышенного кешбэка.

    Args:
        data: Список транзакций в формате словарей
        year: Год для анализа
        month: Месяц для анализа (1-12)

    Returns:
        JSON-строка с суммами кешбэка по категориям
    """
    try:
        # Валидация входных параметров
        if not (1 <= month <= 12):
            raise ValueError("Некорректный номер месяца")

        # Фильтрация транзакций по дате
        filtered_transactions = filter(
            lambda t: _is_transaction_in_period(t, year, month),
            data
        )

        # Явная аннотация типа для аккумулятора
        cashback_by_category: Dict[str, float] = reduce(
            _accumulate_cashback,  # type: ignore[arg-type]
            filtered_transactions,
            {}
        )

        # Сортировка по убыванию кешбэка
        sorted_cashback = dict(sorted(
            cashback_by_category.items(),
            key=lambda item: item[1],
            reverse=True
        ))

        return json.dumps(sorted_cashback, ensure_ascii=False, indent=2)

    except Exception as e:
        logging.error(f"Ошибка анализа: {str(e)}")
        return json.dumps({}, ensure_ascii=False)


def _is_transaction_in_period(
        transaction: Dict[str, Any],
        target_year: int,
        target_month: int
) -> bool:
    """Проверяет принадлежность транзакции к целевому периоду."""
    dt = transaction.get('Дата операции')
    return (
        isinstance(dt, datetime)
        and dt.year == target_year
        and dt.month == target_month
    )


def _accumulate_cashback(
        acc: Dict[str, float],
        transaction: Dict[str, Any]
) -> Dict[str, float]:
    """Аккумулирует кешбэк по категориям."""
    try:
        category = str(transaction.get('Категория', 'Без категории'))
        cashback = float(transaction.get('Кешбэк', 0.0))

        if cashback > 0:
            acc[category] = acc.get(category, 0.0) + cashback
        return acc
    except (TypeError, ValueError) as e:
        logging.warning(f"Ошибка обработки транзакции: {str(e)}")
        return acc
