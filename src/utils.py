import pandas as pd
import requests
import json
import logging
from typing import List, Dict, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


def load_transactions(file_path: str = 'operations.xls') -> List[Dict[str, Any]]:
    """
    Загружает транзакции из Excel-файла с обработкой дат

    Args:
        file_path: Путь к файлу с транзакциями

    Returns:
        Список словарей с транзакциями с строковыми ключами
    """
    try:
        df = pd.read_excel(file_path)

        # Явное преобразование ключей в строки
        transactions = [
            {str(k): v for k, v in record.items()}
            for record in df.to_dict('records')
        ]

        # Обработка дат
        for record in transactions:
            if 'Дата операции' in record:
                try:
                    record['Дата операции'] = pd.to_datetime(
                        record['Дата операции'],
                        dayfirst=True,
                        errors='coerce'
                    ).tz_localize(None)
                except (ValueError, TypeError):
                    record['Дата операции'] = None

        # Фильтрация записей с валидными датами
        valid_transactions = [
            t for t in transactions
            if t.get('Дата операции') is not None and not pd.isna(t['Дата операции'])
        ]

        logging.info(f"Успешно загружено {len(valid_transactions)} транзакций")
        return valid_transactions

    except FileNotFoundError:
        logging.error(f"Файл {file_path} не найден")
        return []
    except Exception as e:
        logging.error(f"Ошибка загрузки данных: {str(e)}")
        return []


def get_currency_rate(currency: str, api_key: str) -> Optional[float]:
    """
    Получает курс валюты через Alpha Vantage API

    Args:
        currency: Код валюты (например, 'USD')
        api_key: API ключ сервиса

    Returns:
        Текущий курс к RUB или None при ошибке
    """
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": currency,
        "to_currency": "RUB",
        "apikey": api_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()

        rate = data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate")
        return round(float(rate), 2) if rate else None

    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        logging.error(f"Ошибка для {currency}: {str(e)}")
        return None


def load_user_settings(file_path: str = 'user_settings.json') -> Dict[str, List[str]]:
    """
    Загружает пользовательские настройки из JSON-файла

    Args:
        file_path: Путь к файлу настроек

    Returns:
        Словарь с настройками с строго типизированными списками строк
    """
    default_settings: Dict[str, List[str]] = {
        'user_currencies': [],
        'user_stocks': []
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            settings: Dict[str, Any] = json.load(f)

        # Валидация и преобразование типов
        return {
            'user_currencies': list(map(str, settings.get('user_currencies', []))),
            'user_stocks': list(map(str, settings.get('user_stocks', [])))
        }

    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logging.error(f"Ошибка загрузки настроек: {str(e)}")
        return default_settings
