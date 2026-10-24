from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import datetime

from app.services.datasets import DatasetValidationError, REQUIRED_COLUMNS, validate_csv


COLUMN_ALIASES = {
    "trade_date": ("trade_date", "date", "日期", "交易日期"),
    "symbol": ("symbol", "ts_code", "code", "股票代码", "证券代码", "代码"),
    "open": ("open", "开盘", "开盘价"),
    "high": ("high", "最高", "最高价"),
    "low": ("low", "最低", "最低价"),
    "close": ("close", "收盘", "收盘价"),
    "volume": ("volume", "vol", "成交量"),
    "amount": ("amount", "成交额", "成交金额"),
    "adj_factor": ("adj_factor", "复权因子"),
    "turnover_rate": ("turnover_rate", "turn", "换手率"),
    "total_mv": ("total_mv", "总市值"),
    "pe": ("pe", "pe_ttm", "pettm", "市盈率", "市盈率ttm"),
}
ALIAS_LOOKUP = {
    alias.strip().lower().replace(" ", ""): canonical
    for canonical, aliases in COLUMN_ALIASES.items()
    for alias in aliases
}
STANDARD_ORDER = ["trade_date", "symbol", "open", "high", "low", "close", "volume", "amount", "adj_factor", "turnover_rate", "total_mv", "pe"]
NUMERIC_COLUMNS = set(STANDARD_ORDER) - {"trade_date", "symbol"}


@dataclass(frozen=True)
class AdaptedCSV:
    content: bytes
    report: dict
    preview: list[dict[str, str]]


def _decode(content: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return content.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    raise DatasetValidationError("CSV必须使用UTF-8、UTF-8 BOM或GB18030编码")


def adapt_cn_stock_csv(content: bytes, preview_limit: int = 10) -> AdaptedCSV:
    text, encoding = _decode(content)
    reader = csv.DictReader(io.StringIO(text))
    raw_columns = reader.fieldnames or []
    if not raw_columns:
        raise DatasetValidationError("CSV缺少表头")
    source_columns = [item.strip() if item else "" for item in raw_columns]
    if any(not item for item in source_columns):
        raise DatasetValidationError("CSV表头包含空字段名")
    if len(source_columns) != len(set(source_columns)):
        raise DatasetValidationError("CSV表头包含重复字段名")
    reader.fieldnames = source_columns
    mapping: dict[str, str] = {}
    reverse: dict[str, str] = {}
    for source in source_columns:
        canonical = ALIAS_LOOKUP.get(source.lower().replace(" ", ""))
        if canonical is None:
            continue
        if canonical in reverse:
            raise DatasetValidationError(f"字段{reverse[canonical]}和{source}都映射到{canonical}，请只保留一个")
        mapping[source] = canonical
        reverse[canonical] = source
    missing = sorted(REQUIRED_COLUMNS - set(reverse))
    if missing:
        raise DatasetValidationError(f"自动映射后仍缺少必填字段：{', '.join(missing)}")

    output_columns = [column for column in STANDARD_ORDER if column in reverse]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=output_columns, lineterminator="\n")
    writer.writeheader()
    converted_rows = 0
    symbol_changes = 0
    date_changes = 0
    preview: list[dict[str, str]] = []
    adjustment_flags: set[str] = set()
    for line, raw in enumerate(reader, start=2):
        if None in raw or any(value is None for value in raw.values()):
            raise DatasetValidationError(f"第{line}行的列数与表头不一致")
        for source in source_columns:
            if source.lower() == "adjustflag":
                flag = (raw.get(source) or "").strip()
                if flag not in {"1", "2", "3"}:
                    raise DatasetValidationError(f"第{line}行的adjustflag必须是1、2或3")
                adjustment_flags.add(flag)
        row = {canonical: (raw.get(source) or "").strip() for source, canonical in mapping.items()}
        for column in NUMERIC_COLUMNS & set(row):
            row[column] = _normalize_number(row[column], column)
        original_date, original_symbol = row["trade_date"], row["symbol"]
        try:
            row["trade_date"] = normalize_trade_date(original_date)
            row["symbol"] = normalize_symbol(original_symbol)
        except ValueError as exc:
            raise DatasetValidationError(f"第{line}行转换失败：{exc}") from exc
        date_changes += row["trade_date"] != original_date
        symbol_changes += row["symbol"] != original_symbol
        writer.writerow(row)
        converted_rows += 1
        if len(preview) < max(1, min(preview_limit, 50)):
            preview.append(dict(row))
    if converted_rows == 0:
        raise DatasetValidationError("CSV不包含数据行")
    if len(adjustment_flags) > 1:
        raise DatasetValidationError("CSV混用了不同复权状态，请按同一口径重新导出")
    adapted = stream.getvalue().encode("utf-8")
    parsed = validate_csv(adapted)
    dropped = [column for column in source_columns if column not in mapping]
    warnings = []
    if "volume" in reverse:
        warnings.append("请确认成交量单位（股或手）与原始数据源说明一致。")
    if "turnover_rate" in reverse:
        warnings.append("换手率保留原始数值，未自动判断百分数或小数口径。")
    if adjustment_flags:
        warnings.append("adjustflag表示价格复权状态，已记录为来源元数据，不转换为adj_factor；任务默认使用导入的close。")
    if parsed.report["weekend_row_count"]:
        warnings.append(
            f"标准化数据含{parsed.report['weekend_date_count']}个周末日期、"
            f"{parsed.report['weekend_row_count']}行行情；请在导入前核对源文件日期。"
        )
    if parsed.report["announced_weekday_closure_row_count"]:
        warnings.append(
            f"标准化数据含{parsed.report['announced_weekday_closure_date_count']}个沪深交易所公告休市工作日、"
            f"{parsed.report['announced_weekday_closure_row_count']}行行情；请在导入前核对源文件日期。"
        )
    if parsed.report["calendar_uncovered_years"]:
        warnings.append(
            f"离线公告休市表未覆盖{','.join(map(str, parsed.report['calendar_uncovered_years']))}年；"
            "这些年份未做公告休市核对。"
        )
    return AdaptedCSV(
        content=adapted,
        preview=preview,
        report={
            "adapter": "cn_stock_csv_auto",
            "adapter_version": "1.3.1",
            "source_adjustment_flags": sorted(adjustment_flags),
            "source_encoding": encoding,
            "source_columns": source_columns,
            "column_mapping": mapping,
            "output_columns": output_columns,
            "dropped_columns": dropped,
            "converted_rows": converted_rows,
            "normalized_symbol_rows": symbol_changes,
            "normalized_date_rows": date_changes,
            "validation": {"row_count": parsed.row_count, "symbol_count": parsed.symbol_count,
                           "start_date": parsed.start_date.isoformat(), "end_date": parsed.end_date.isoformat(),
                           "weekend_date_count": parsed.report["weekend_date_count"],
                           "weekend_row_count": parsed.report["weekend_row_count"],
                           "announced_closure_calendar_version": parsed.report["announced_closure_calendar_version"],
                           "announced_weekday_closure_date_count": parsed.report["announced_weekday_closure_date_count"],
                           "announced_weekday_closure_row_count": parsed.report["announced_weekday_closure_row_count"],
                           "announced_weekday_closure_dates": parsed.report["announced_weekday_closure_dates"],
                           "calendar_uncovered_years": parsed.report["calendar_uncovered_years"]},
            "warnings": warnings,
        },
    )


def normalize_trade_date(value: str) -> str:
    cleaned = value.strip()
    for pattern in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(cleaned, pattern).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"日期{value!r}无法识别")


def normalize_symbol(value: str) -> str:
    cleaned = value.strip().upper()
    matches = re.fullmatch(r"(\d{6})\.(SZ|SH|BJ)", cleaned)
    if matches:
        return cleaned
    matches = re.fullmatch(r"(SZ|SH|BJ)[.]?(\d{6})", cleaned)
    if matches:
        return f"{matches.group(2)}.{matches.group(1)}"
    matches = re.fullmatch(r"(\d{6})[.]?(SZ|SH|BJ)", cleaned)
    if matches:
        return f"{matches.group(1)}.{matches.group(2)}"
    if re.fullmatch(r"\d{6}", cleaned):
        if cleaned.startswith(("4", "8", "92")):
            market = "BJ"
        elif cleaned.startswith(("5", "6", "9")):
            market = "SH"
        else:
            market = "SZ"
        return f"{cleaned}.{market}"
    raise ValueError(f"证券代码{value!r}无法识别")


def _normalize_number(value: str, column: str) -> str:
    cleaned = value.strip()
    if cleaned.lower() in {"", "--", "none", "null", "nan", "n/a"}:
        return ""
    cleaned = cleaned.replace(",", "")
    if cleaned.endswith("%"):
        if column != "turnover_rate":
            raise DatasetValidationError(f"字段{column}不应包含百分号")
        cleaned = cleaned[:-1].strip()
    return cleaned
