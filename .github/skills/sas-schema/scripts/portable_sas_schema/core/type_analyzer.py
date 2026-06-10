"""Data-type heuristics for the portable sas-schema bundle."""

import re
from typing import Any, Optional

import pandas as pd

from .date_analyzer import DateFormatAnalyzer


class DataTypeAnalyzer:
    """Infer SAS character vs numeric types from metadata and data samples."""

    def __init__(self, date_analyzer: Optional[DateFormatAnalyzer] = None):
        self.date_analyzer = date_analyzer or DateFormatAnalyzer()

    def get_sas_data_type(self, col_name: str, df: pd.DataFrame, meta: Any, debug: bool = False) -> str:
        type_evidence = {}

        if re.search(r"(DTC$|DATE$)", col_name, re.IGNORECASE):
            type_evidence["name_pattern"] = "character"

        if hasattr(meta, "column_types") and isinstance(meta.column_types, dict):
            col_type = meta.column_types.get(col_name)
            if col_type:
                type_evidence["column_types"] = "character" if col_type == "string" else "numeric"

        if hasattr(meta, "readstat_variable_types") and isinstance(meta.readstat_variable_types, dict):
            var_type = meta.readstat_variable_types.get(col_name)
            if var_type:
                type_evidence["readstat_variable_types"] = "character" if var_type == "string" else "numeric"

        col_format = getattr(meta, "formats", {}).get(col_name, "")
        if col_format:
            if col_format.startswith("$"):
                type_evidence["format"] = "character"
            elif any(pattern in col_format.upper() for pattern in ["DATE", "DATETIME", "TIME"]):
                type_evidence["format"] = "numeric"
            elif any(pattern in col_format.upper() for pattern in ["F", "E", "COMMA", "DOLLAR", "PERCENT"]):
                type_evidence["format"] = "numeric"

        if hasattr(meta, "variable_value_labels") and isinstance(meta.variable_value_labels, dict):
            if col_name in meta.variable_value_labels:
                type_evidence["variable_value_labels"] = "numeric"

        sample = df[col_name].dropna().head(20)
        if len(sample) > 0:
            try:
                sample.astype(float)
                type_evidence["data_numeric_castable"] = "numeric"
            except Exception:
                type_evidence["data_numeric_castable"] = "character"

            if self.date_analyzer.has_date_pattern_evidence(col_name, df[col_name]):
                type_evidence["date_patterns"] = "character"

        type_evidence["pandas_dtype"] = "numeric" if pd.api.types.is_numeric_dtype(df[col_name]) else "character"

        if debug:
            print(f"Type evidence for {col_name}: {type_evidence}")

        if "column_types" in type_evidence:
            return type_evidence["column_types"]
        if "readstat_variable_types" in type_evidence:
            return type_evidence["readstat_variable_types"]
        if "format" in type_evidence:
            return type_evidence["format"]
        if "name_pattern" in type_evidence and type_evidence["name_pattern"] == "character":
            if "date_patterns" in type_evidence:
                return type_evidence["date_patterns"]
            return "character"
        if "date_patterns" in type_evidence:
            return type_evidence["date_patterns"]
        return type_evidence["pandas_dtype"]

    def is_id_like_column(self, col_name: str, values: pd.Series) -> bool:
        flag_name_patterns = [
            r"FL$",
            r"YN\d*$",
            r"(Y|N)NUL+$",
            r"EXIST$",
            r"OCCUR$",
            r"CONF$",
            r"DONE$",
            r"EVNT$",
            r"EVENT$",
            r"DCSN$",
            r"DETH$",
            r"FLAG$",
            r"IND$",
        ]
        if any(re.search(pattern, col_name, re.IGNORECASE) for pattern in flag_name_patterns):
            return False

        non_null = values.dropna()
        sample = non_null.astype(str).sample(min(100, len(non_null))).tolist() if len(non_null) > 0 else []
        if len(sample) > 0:
            unique_values = set(str(value).strip().upper() for value in sample)
            flag_value_patterns = [
                {"Y", "N"},
                {"YES", "NO"},
                {"TRUE", "FALSE"},
                {"T", "F"},
                {"0", "1"},
                {"Y", "N", "U"},
                {"Y", "N", ""},
                {"Y", "N", "NA"},
            ]
            if len(unique_values) <= 5 and any(unique_values.issubset(pattern) for pattern in flag_value_patterns):
                return False

        id_name_patterns = [
            r"ID$",
            r"_ID$",
            r"^ID",
            r"^ID_",
            r"NUM$",
            r"NUMBER$",
            r"^SUBJ",
            r"^SUBJID",
            r"^SITE",
            r"^SITEID",
            r"^PATIENT",
            r"^PAT_ID",
            r"^VISIT",
            r"^VIS_",
            r"^USUBJID$",
            r"^STUDYID$",
        ]
        if any(re.search(pattern, col_name, re.IGNORECASE) for pattern in id_name_patterns):
            return True

        if len(sample) > 5:
            unique_ratio = len(set(sample)) / len(sample)
            if unique_ratio > 0.9 and len(sample) > 10:
                lengths = [len(str(value)) for value in sample]
                consistent_length = len(set(lengths)) <= 3
                prefixed_number_pattern = re.compile(r"^[A-Z]{1,5}\d{3,}$")
                segmented_pattern = re.compile(r"^[A-Z0-9]+-[A-Z0-9]+-\d{2,}$")
                subject_id_pattern = re.compile(r"^(\d{3,}-\d{3,}|\d{3,})$")
                prefixed_number_ratio = sum(1 for value in sample if prefixed_number_pattern.search(str(value).upper())) / len(sample)
                segmented_ratio = sum(1 for value in sample if segmented_pattern.search(str(value).upper())) / len(sample)
                subject_id_ratio = sum(1 for value in sample if subject_id_pattern.search(str(value))) / len(sample)
                if consistent_length and (
                    prefixed_number_ratio > 0.5
                    or segmented_ratio > 0.5
                    or subject_id_ratio > 0.5
                ):
                    return True

        return False

    def is_result_column(self, col_name: str, values: pd.Series) -> bool:
        result_name_patterns = [
            r"RESULT$",
            r"VALUE$",
            r"MEASURE$",
            r"READING$",
            r"FINDING$",
            r"LBORRES",
            r"VSORRES",
            r"QSORRES",
            r"ECGORRES",
        ]
        if any(re.search(pattern, col_name, re.IGNORECASE) for pattern in result_name_patterns):
            return True

        non_null = values.dropna()
        sample = non_null.astype(str).sample(min(100, len(non_null))).tolist() if len(non_null) > 0 else []
        if len(sample) < 5:
            return False

        if pd.api.types.is_numeric_dtype(values):
            unique_ratio = values.nunique() / len(non_null)
            if unique_ratio > 0.95 and len(non_null) > 5:
                return True

        measurement_pattern = re.compile(r"^\s*\d+\.\d+\s*([a-zA-Z%/]+)?\s*$")
        measurement_ratio = sum(1 for value in sample if measurement_pattern.match(str(value))) / len(sample)
        numeric_decimal_pattern = re.compile(r"^\s*\d+\.\d+\s*$")
        numeric_decimal_ratio = sum(1 for value in sample if numeric_decimal_pattern.match(str(value))) / len(sample)
        result_text_pattern = re.compile(
            r"^(normal|abnormal|positive|negative|present|absent|detected|not detected|elevated|low|high|within normal limits)$",
            re.IGNORECASE,
        )
        result_text_ratio = sum(1 for value in sample if result_text_pattern.match(str(value).strip())) / len(sample)

        if pd.api.types.is_numeric_dtype(values) and len(values.dropna()) > 10:
            numeric_values = pd.to_numeric(values.dropna(), errors="coerce").dropna()
            if len(numeric_values) > 10:
                has_decimals = any(
                    float(value) != int(float(value))
                    for value in numeric_values.sample(min(20, len(numeric_values)))
                )
                value_range = numeric_values.max() - numeric_values.min()
                if has_decimals and value_range > 10:
                    return True

        return (
            measurement_ratio > 0.7
            or numeric_decimal_ratio > 0.7
            or result_text_ratio > 0.7
        )