import pandas as pd
from datetime import datetime
from typing import Optional, Callable, Any
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def _save_report(data: pd.DataFrame, filename: str) -> None:
    """Сохраняет DataFrame в JSON файл."""
    try:
        data.to_json(filename, orient='records', force_ascii=False, indent=4)
        logger.info(f"Отчет сохранен в {filename}")
    except Exception as e:
        logger.error(f"Ошибка сохранения отчета: {e}")
        raise


def save_report(
    filename: Optional[str] = None
) -> Callable[[Callable[..., pd.DataFrame]], Callable[..., pd.DataFrame]]:
    """Декоратор для сохранения отчета в файл."""

    def decorator(func: Callable[..., pd.DataFrame]) -> Callable[..., pd.DataFrame]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
            result = func(*args, **kwargs)
            output_file = filename if filename else f"{func.__name__}_report.json"
            _save_report(result, output_file)
            return result

        return wrapper

    return decorator


@save_report()
def spending_by_category(
        transactions: pd.DataFrame,
        category: str,
        date: Optional[str] = None
) -> pd.DataFrame:
    """
    Возвращает траты по заданной категории за последние три месяца от указанной даты.
    """
    current_date = pd.to_datetime(date) if date else pd.to_datetime(datetime.now())
    start_date = current_date - pd.DateOffset(months=3)

    # Фильтрация по категории
    category_transactions = transactions[transactions['Категория'] == category].copy()
    category_transactions['Дата операции'] = pd.to_datetime(
        category_transactions['Дата операции']
    )

    # Фильтрация по датам
    date_mask = \
        (category_transactions['Дата операции'] >= start_date) \
        & (category_transactions['Дата операции'] <= current_date)
    filtered = category_transactions.loc[date_mask]

    if filtered.empty:
        return pd.DataFrame(columns=['Месяц', 'Сумма операции'])

    # Группировка по месяцам
    filtered['Месяц'] = filtered['Дата операции'].dt.strftime('%Y-%m')
    grouped: pd.DataFrame = filtered.groupby('Месяц', as_index=False).agg({'Сумма операции': 'sum'})

    return grouped
