import pytest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import pandas as pd
import requests
from src.utils import load_transactions, get_currency_rate, load_user_settings


@pytest.fixture
def mock_excel_data() -> Dict[str, Any]:
    """Фикстура с тестовыми данными для Excel"""
    return {
        'Дата операции': ['15-05-2023 00:00:00', 'invalid_date'],
        'Номер карты': ['1234****5678', '9876****5432'],
        'Сумма операции': [1000.0, 500.0],
        'Кешбэк': [10.0, 5.0]
    }


@pytest.fixture
def mock_excel_file(mock_excel_data: Dict[str, Any], tmp_path: Path) -> str:
    """Генерирует тестовый Excel-файл"""
    file_path = tmp_path / "test_operations.xlsx"
    df = pd.DataFrame(mock_excel_data)
    df.to_excel(file_path, index=False, engine='openpyxl')
    return str(file_path)


@pytest.mark.parametrize("file_exists,expected_count", [
    (True, 1),
    (False, 0)
])
def test_load_transactions(mock_excel_file: str, file_exists: bool, expected_count: int) -> None:
    test_file = mock_excel_file if file_exists else "invalid_path.xlsx"
    result = load_transactions(test_file)
    assert len(result) == expected_count
    if expected_count > 0:
        assert isinstance(result[0]['Дата операции'], datetime)


def test_load_transactions_data_processing(mock_excel_file: str) -> None:
    result = load_transactions(mock_excel_file)
    assert len(result) == 1
    assert isinstance(result[0]['Дата операции'], datetime)
    assert result[0]['Дата операции'].year == 2023
    assert result[0]['Дата операции'].month == 5


@pytest.mark.parametrize("api_response,expected", [
    ({'Realtime Currency Exchange Rate': {'5. Exchange Rate': '75.5'}}, 75.5),
    ({}, None),
    (requests.exceptions.RequestException("Connection error"), None)
])
def test_get_currency_rate(api_response: Any, expected: Optional[float]) -> None:
    with patch('requests.get') as mock_get, \
            patch('logging.error') as mock_logging:

        if isinstance(api_response, Exception):
            mock_get.side_effect = api_response
        else:
            mock_response = MagicMock()
            mock_response.json.return_value = api_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

        result = get_currency_rate('USD', 'test_api_key')
        assert result == expected

        if isinstance(api_response, Exception):
            mock_logging.assert_called()


@pytest.mark.parametrize("file_content,expected", [
    (
        '{"user_currencies": ["USD", 123], "user_stocks": ["AAPL"]}',
        {'user_currencies': ['USD', '123'], 'user_stocks': ['AAPL']}
    ),
    (
        'invalid_json',
        {'user_currencies': [], 'user_stocks': []}
    ),
    (
        '{"other_key": "value"}',
        {'user_currencies': [], 'user_stocks': []}
    )
])
def test_load_user_settings(file_content: str, expected: Dict[str, List[str]]) -> None:
    with patch('builtins.open', mock_open(read_data=file_content)):
        result = load_user_settings()
        assert result == expected


def test_load_user_settings_file_not_found() -> None:
    with patch('builtins.open', side_effect=FileNotFoundError()), \
            patch('logging.error') as mock_logging:
        result = load_user_settings()
        assert result == {'user_currencies': [], 'user_stocks': []}
        mock_logging.assert_called()
