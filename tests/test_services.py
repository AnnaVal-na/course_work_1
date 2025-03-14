import unittest
from unittest.mock import patch, MagicMock
from src.services import analyze_cashback_categories, _is_transaction_in_period, _accumulate_cashback
from datetime import datetime
import json
from typing import Any, Dict, List


class TestServices(unittest.TestCase):

    @patch("src.services._is_transaction_in_period")  # Мокируем функцию
    def test_analyze_cashback_categories(self, mock_is_transaction_in_period: MagicMock) -> None:
        """
        Тестирование функции analyze_cashback_categories.
        """
        # Генерация тестовых данных
        test_data: List[Dict[str, Any]] = [  # Добавлена аннотация типа для тестовых данных
            {"Дата операции": datetime(2023, 10, 5), "Категория": "Еда", "Кешбэк": 10.5},
            {"Дата операции": datetime(2023, 10, 15), "Категория": "Транспорт", "Кешбэк": 5.0},
            {"Дата операции": datetime(2023, 9, 20), "Категория": "Еда", "Кешбэк": 7.5},
            {"Дата операции": datetime(2023, 10, 25), "Категория": "Еда", "Кешбэк": 12.0},
        ]

        # Настройка мока для фильтрации транзакций
        mock_is_transaction_in_period.side_effect = lambda t, y, m: (
            t["Дата операции"].year == y and t["Дата операции"].month == m
        )

        # Вызов функции
        result: str = analyze_cashback_categories(test_data, 2023, 10)

        # Проверка результатов
        expected_result: Dict[str, float] = {  # Добавлена аннотация типа для ожидаемого результата
            "Еда": 22.5,
            "Транспорт": 5.0
        }
        self.assertEqual(json.loads(result), expected_result)

    def test_is_transaction_in_period(self) -> None:
        """
        Тестирование функции _is_transaction_in_period.
        """
        # Тестовые данные
        transaction_in_period: Dict[str, Any] = {"Дата операции": datetime(2023, 10, 15)}
        transaction_out_of_period: Dict[str, Any] = {"Дата операции": datetime(2023, 9, 15)}

        # Проверка транзакции внутри периода
        self.assertTrue(_is_transaction_in_period(transaction_in_period, 2023, 10))

        # Проверка транзакции вне периода
        self.assertFalse(_is_transaction_in_period(transaction_out_of_period, 2023, 10))

    def test_accumulate_cashback(self) -> None:
        """
        Тестирование функции _accumulate_cashback.
        """
        # Начальный аккумулятор
        accumulator: Dict[str, float] = {}

        # Тестовая транзакция
        transaction: Dict[str, Any] = {"Категория": "Еда", "Кешбэк": 10.5}

        # Аккумулирование кешбэка
        result: Dict[str, float] = _accumulate_cashback(accumulator, transaction)

        # Проверка результата
        self.assertEqual(result, {"Еда": 10.5})

        # Добавление второй транзакции
        transaction2: Dict[str, Any] = {"Категория": "Еда", "Кешбэк": 5.0}
        result = _accumulate_cashback(result, transaction2)
        self.assertEqual(result, {"Еда": 15.5})

        # Транзакция с новой категорией
        transaction3: Dict[str, Any] = {"Категория": "Транспорт", "Кешбэк": 7.5}
        result = _accumulate_cashback(result, transaction3)
        self.assertEqual(result, {"Еда": 15.5, "Транспорт": 7.5})


if __name__ == "__main__":
    unittest.main()
