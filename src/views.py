import json
from datetime import datetime
from typing import Dict, Optional
import requests
from .utils import load_transactions

API_KEY = '4JKBVMLEJ1NE3AIX'


def get_currency_rate(currency: str) -> Optional[float]:
    """Получает текущий курс валюты к рублю через Alpha Vantage API."""
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'CURRENCY_EXCHANGE_RATE',
        'from_currency': currency,
        'to_currency': 'RUB',
        'apikey': API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        rate = data.get('Realtime Currency Exchange Rate', {}).get('5. Exchange Rate')
        return float(rate) if rate else None
    except Exception as e:
        print(f"Ошибка получения курса {currency}: {e}")
        return None


def get_stock_price(symbol: str) -> Optional[float]:
    """Получает текущую цену акции из S&P 500 через Alpha Vantage API."""
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get('Global Quote', {}).get('05. price')
        return float(price) if price else None
    except Exception as e:
        print(f"Ошибка получения цены акции {symbol}: {e}")
        return None


def home_view(input_datetime: str) -> str:
    """
    Генерирует JSON-ответ для главной страницы.

    Args:
        input_datetime (str): Дата и время в формате 'YYYY-MM-DD HH:MM:SS'.

    Returns:
        str: JSON-строка с данными для отображения.
    """
    try:
        # Парсинг входной даты
        input_dt = datetime.strptime(input_datetime, '%Y-%m-%d %H:%M:%S')
        start_of_month = input_dt.replace(day=1, hour=0, minute=0, second=0)

        # Загрузка и фильтрация транзакций
        transactions = load_transactions()
        filtered = [
            t for t in transactions
            if start_of_month <= t['Дата операции'] <= input_dt
        ]

        # Обработка данных по картам
        cards: Dict[str, Dict[str, float]] = {}
        for t in filtered:
            last_digits = str(t['Номер карты'])[-4:]
            cards.setdefault(last_digits, {'total_spent': 0.0, 'cashback': 0.0})
            cards[last_digits]['total_spent'] += t['Сумма операции']
            cards[last_digits]['cashback'] += t['Сумма операции'] / 100  # 1% кешбэк

        # Формирование списка карт
        cards_list = [
            {
                'last_digits': k,
                'total_spent': round(v['total_spent'], 2),
                'cashback': round(v['cashback'], 2)
            }
            for k, v in cards.items()
        ]

        # Топ-5 транзакций
        sorted_transactions = sorted(
            filtered,
            key=lambda x: abs(x['Сумма платежа']),
            reverse=True
        )[:5]

        top_transactions = [
            {
                'date': t['Дата операции'].strftime('%d.%m.%Y'),
                'amount': t['Сумма платежа'],
                'category': t['Категория'],
                'description': t['Описание']
            }
            for t in sorted_transactions
        ]

        # Загрузка настроек
        try:
            with open('user_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = {'user_currencies': [], 'user_stocks': []}

        # Получение курсов валют
        currency_rates = [
            {'currency': curr, 'rate': rate}
            for curr in settings['user_currencies']
            if (rate := get_currency_rate(curr)) is not None
        ]

        # Получение цен акций
        stock_prices = [
            {'stock': stock, 'price': price}
            for stock in settings['user_stocks']
            if (price := get_stock_price(stock)) is not None
        ]

        # Определение приветствия
        hour = input_dt.hour
        greeting = (
            'Доброе утро' if 5 <= hour < 12 else
            'Добрый день' if 12 <= hour < 18 else
            'Добрый вечер' if 18 <= hour < 23 else
            'Доброй ночи'
        )

        # Формирование ответа
        return json.dumps(
            {
                'greeting': greeting,
                'cards': cards_list,
                'top_transactions': top_transactions,
                'currency_rates': currency_rates,
                'stock_prices': stock_prices
            },
            ensure_ascii=False,
            indent=2
        )

    except ValueError as e:
        return json.dumps({'error': f'Ошибка формата даты: {e}'}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({'error': f'Системная ошибка: {e}'}, ensure_ascii=False)
