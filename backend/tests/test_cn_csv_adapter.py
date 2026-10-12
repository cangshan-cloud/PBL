import csv
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.cn_csv_adapter import adapt_cn_stock_csv, normalize_symbol, normalize_trade_date
from app.services.datasets import DatasetValidationError, validate_csv


class ChinaStockCsvAdapterTests(unittest.TestCase):
    def test_adapts_tushare_style_columns_and_values(self):
        source = """ts_code,trade_date,open,high,low,close,vol,amount,turnover_rate,total_mv,pe
000001.SZ,20250102,10,11,9,10.5,1000,10500,1.2,100000,8.5
600000.SH,20250102,8,8.5,7.8,8.2,900,7380,0.8,200000,6.2
""".encode()
        adapted = adapt_cn_stock_csv(source)
        parsed = validate_csv(adapted.content)
        self.assertEqual(parsed.row_count, 2)
        self.assertEqual(adapted.report["column_mapping"]["ts_code"], "symbol")
        self.assertEqual(adapted.preview[0]["trade_date"], "2025-01-02")
        self.assertEqual(adapted.preview[0]["symbol"], "000001.SZ")
        self.assertIn("换手率保留原始数值", adapted.report["warnings"][1])

    def test_adapts_gb18030_chinese_export(self):
        source = """日期,股票代码,开盘,最高,最低,收盘,成交量,成交额,无关列
2025/01/02,600000,8,8.5,7.8,8.2,"1,000",7380,ignored
""".encode("gb18030")
        adapted = adapt_cn_stock_csv(source)
        self.assertEqual(adapted.report["source_encoding"], "gb18030")
        self.assertEqual(adapted.preview[0]["symbol"], "600000.SH")
        self.assertEqual(adapted.preview[0]["volume"], "1000")
        self.assertEqual(adapted.report["dropped_columns"], ["无关列"])

    def test_normalizes_common_symbol_and_date_forms(self):
        self.assertEqual(normalize_symbol("sh.600000"), "600000.SH")
        self.assertEqual(normalize_symbol("000001"), "000001.SZ")
        self.assertEqual(normalize_symbol("920001"), "920001.BJ")
        self.assertEqual(normalize_trade_date("2025.01.02"), "2025-01-02")

    def test_rejects_ambiguous_duplicate_mapping(self):
        content = b"date,trade_date,code,close\n2025-01-02,20250102,000001,10\n"
        with self.assertRaisesRegex(DatasetValidationError, "trade_date"):
            adapt_cn_stock_csv(content)

    def test_output_is_utf8_standard_csv(self):
        source = "日期,代码,收盘\n20250102,000001,10\n".encode("utf-8")
        adapted = adapt_cn_stock_csv(source)
        rows = list(csv.DictReader(io.StringIO(adapted.content.decode("utf-8"))))
        self.assertEqual(rows, [{"trade_date": "2025-01-02", "symbol": "000001.SZ", "close": "10"}])

    def test_adjustment_status_is_not_a_price_multiplier(self):
        source = b"date,code,close,adjustflag\n2025-01-02,sh.600000,10,2\n"
        adapted = adapt_cn_stock_csv(source)
        self.assertNotIn("adj_factor", adapted.report["output_columns"])
        self.assertEqual(adapted.report["source_adjustment_flags"], ["2"])
        self.assertEqual(adapted.preview[0]["close"], "10")

    def test_rejects_mixed_adjustment_states(self):
        source = b"date,code,close,adjustflag\n2025-01-02,sh.600000,10,2\n2025-01-03,sh.600000,11,3\n"
        with self.assertRaisesRegex(DatasetValidationError, "复权状态"):
            adapt_cn_stock_csv(source)

    def test_rejects_extra_cells_before_dropping_unknown_columns(self):
        with self.assertRaisesRegex(DatasetValidationError, "列数"):
            adapt_cn_stock_csv(b"date,code,close\n20250102,000001,10,extra\n")


if __name__ == "__main__":
    unittest.main()
