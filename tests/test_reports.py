import unittest
from unittest.mock import patch, MagicMock
from pandas import DataFrame
import pandas as pd
from src.reports import spending_by_category


class TestReports(unittest.TestCase):
    def setUp(self) -> None:
        self.transactions = DataFrame({
            "Категория": ["Супермаркеты", "Супермаркеты", "Транспорт"],
            "Дата операции": ["2023-03-15", "2023-04-10", "2023-05-15"],
            "Сумма операции": [-100, -200, -50]
        })
        self.transactions["Дата операции"] = pd.to_datetime(
            self.transactions["Дата операции"]
        )

    @patch("src.reports._save_report")
    def test_spending_by_category_custom_date(self, mock_save_report: MagicMock) -> None:
        expected = DataFrame({
            "Месяц": ["2023-03", "2023-04"],
            "Сумма операции": [-100, -200]
        })
        result = spending_by_category(self.transactions, "Супермаркеты", "2023-05-15")
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True),
            expected.reset_index(drop=True)
        )
        mock_save_report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
