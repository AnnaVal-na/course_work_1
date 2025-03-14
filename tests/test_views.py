import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
from src.views import home_view


@pytest.fixture
def mock_transactions() -> List[Dict[str, Any]]:
    """Фикстура с тестовыми транзакциями"""
    return [
        {
            'Дата операции': datetime(2023, 5, 15),
            'Номер карты': '1234567890123456',
            'Сумма операции': 1000.0,
            'Кешбэк': 10.0,
            'Категория': 'Супермаркеты',
            'Описание': 'Покупка в магазине',
            'Сумма платежа': 1000.0
        }
    ]


@pytest.fixture
def mock_settings_content() -> str:
    """Фикстура с содержимым файла настроек"""
    return json.dumps({
        'user_currencies': ['USD', 'EUR'],
        'user_stocks': ['AAPL', 'TSLA']
    })


@pytest.mark.parametrize("input_date,expected_greeting", [
    ('2023-05-20 09:00:00', 'Доброе утро'),
    ('2023-05-20 14:00:00', 'Добрый день'),
    ('2023-05-20 20:00:00', 'Добрый вечер'),
    ('2023-05-20 23:30:00', 'Доброй ночи'),
])
def test_greeting_logic(
        input_date: str,
        expected_greeting: str,
        mock_settings_content: str
) -> None:
    """Тестирование логики формирования приветствия"""
    with patch('src.views.load_transactions', return_value=[]), \
            patch('src.views.get_currency_rate') as mock_currency, \
            patch('src.views.get_stock_price') as mock_stock, \
            patch('builtins.open', mock_open(read_data=mock_settings_content)):
        mock_currency.return_value = 75.0
        mock_stock.return_value = 150.0

        result = json.loads(home_view(input_date))
        assert 'greeting' in result
        assert result['greeting'] == expected_greeting


def test_cards_calculation(
        mock_transactions: List[Dict[str, Any]],
        mock_settings_content: str
) -> None:
    """Тестирование расчета данных по картам"""
    with patch('src.views.load_transactions', return_value=mock_transactions), \
            patch('src.views.get_currency_rate', return_value=75.0), \
            patch('src.views.get_stock_price', return_value=100.0), \
            patch('builtins.open', mock_open(read_data=mock_settings_content)):
        result = json.loads(home_view('2023-05-20 12:00:00'))

        assert 'cards' in result
        assert len(result['cards']) == 1
        assert result['cards'][0]['last_digits'] == '3456'
        assert result['cards'][0]['total_spent'] == 1000.0
        assert result['cards'][0]['cashback'] == 10.0


@pytest.mark.parametrize("api_response,expected", [
    ({'Realtime Currency Exchange Rate': {'5. Exchange Rate': '75.5'}}, 75.5),
    ({}, None),
    (None, None)
])
def test_currency_rates(
        api_response: Optional[Dict[str, Any]],
        expected: Optional[float],
        mock_settings_content: str
) -> None:
    """Параметризованный тест для API курсов валют"""
    mock_response = MagicMock()
    mock_response.json.return_value = api_response

    with patch('src.views.requests.get', return_value=mock_response), \
            patch('src.views.load_transactions', return_value=[]), \
            patch('builtins.open', mock_open(read_data=mock_settings_content)):

        result = json.loads(home_view('2023-05-20 12:00:00'))

        if expected:
            assert 'currency_rates' in result
            assert any(r['rate'] == expected for r in result['currency_rates'])
        else:
            assert len(result.get('currency_rates', [])) == 0


def test_error_handling() -> None:
    """Тестирование обработки ошибок"""
    with patch('src.views.load_transactions', side_effect=Exception("DB Error")):
        result = json.loads(home_view('2023-05-20 12:00:00'))
        assert 'error' in result
        assert "DB Error" in result['error']


def test_empty_transactions(mock_settings_content: str) -> None:
    """Тестирование пустого набора транзакций"""
    with patch('src.views.load_transactions', return_value=[]), \
            patch('builtins.open', mock_open(read_data=mock_settings_content)):
        result = json.loads(home_view('2023-05-20 12:00:00'))
        assert 'cards' in result
        assert len(result['cards']) == 0
        assert 'top_transactions' in result
        assert len(result['top_transactions']) == 0


def test_invalid_date_format() -> None:
    """Тестирование неверного формата даты"""
    result = json.loads(home_view('invalid-date'))
    assert 'error' in result
    assert 'формата даты' in result['error']
