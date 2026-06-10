"""Portable analyze/list engine for the sas-schema skill bundle."""

import os
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pyreadstat

from .date_analyzer import DateFormatAnalyzer
from .type_analyzer import DataTypeAnalyzer


_SAS_FILE_GLOB = "*.sas7bdat"
_SAS_FILE_EXT = ".sas7bdat"
_ENCODING_FALLBACKS: tuple = ("latin1",)


def _read_sas7bdat_with_fallback(file_path: str):
    try:
        df, meta = pyreadstat.read_sas7bdat(file_path)
        return df, meta, None
    except UnicodeDecodeError:
        last_error = None
        for encoding in _ENCODING_FALLBACKS:
            try:
                df, meta = pyreadstat.read_sas7bdat(file_path, encoding=encoding)
                return df, meta, encoding
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
        raise last_error


class SasSchemaAnalyzer:
    """Portable SAS schema analysis engine."""

    def __init__(self, code_list_threshold: float = 0.15, debug: bool = False):
        self.code_list_threshold = code_list_threshold
        self.debug = debug
        self.date_analyzer = DateFormatAnalyzer()
        self.type_analyzer = DataTypeAnalyzer(self.date_analyzer)

    @staticmethod
    def _find_sas_files(root: str, recursive: bool, max_files: int = 0) -> list:
        found = []
        if recursive:
            for path in Path(root).rglob(_SAS_FILE_GLOB):
                found.append(str(path))
                if max_files and len(found) >= max_files:
                    break
        else:
            for name in os.listdir(root):
                if name.lower().endswith(_SAS_FILE_EXT):
                    found.append(os.path.join(root, name))
                    if max_files and len(found) >= max_files:
                        break
        return found

    async def analyze_file(self, file_path: str, ctx: Any = None) -> Dict[str, Any]:
        try:
            file_path = os.path.normpath(file_path)

            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "File not found",
                    "file_path": file_path,
                }

            if ctx:
                await ctx.info(f"Reading SAS file: {os.path.basename(file_path)}")
                await ctx.report_progress(10, 100, "Reading file...")

            df, meta, used_encoding = _read_sas7bdat_with_fallback(file_path)

            if ctx:
                await ctx.report_progress(50, 100, "Analyzing schema...")

            row_count = len(df)
            nunique_counts = df.nunique()
            schema = {
                "success": True,
                "file_path": file_path,
                "row_count": row_count,
                "column_count": len(df.columns),
                "file_label": getattr(meta, "file_label", None),
                "used_encoding": used_encoding,
                "columns": [],
            }

            for col_name in df.columns:
                unique_count = int(nunique_counts[col_name])
                column_label = meta.column_names_to_labels.get(col_name, None)
                col_info = {
                    "name": col_name,
                    "label": column_label,
                    "unique_count": unique_count,
                }

                col_info["sas_data_type"] = self.type_analyzer.get_sas_data_type(
                    col_name,
                    df,
                    meta,
                    self.debug,
                )

                if self.date_analyzer.has_date_metadata_evidence(col_name, column_label):
                    date_analysis = self.date_analyzer.analyze_date_series(df[col_name])
                    if date_analysis.get("is_date", False):
                        col_info["date_format_analysis"] = date_analysis

                low_cardinality = unique_count <= 20
                below_threshold = row_count <= 20 or (
                    row_count > 0 and unique_count / row_count < self.code_list_threshold
                )

                if (
                    low_cardinality
                    and below_threshold
                    and not self.type_analyzer.is_id_like_column(col_name, df[col_name])
                    and not self.type_analyzer.is_result_column(col_name, df[col_name])
                ):
                    value_counts = df[col_name].value_counts(dropna=False).to_dict()
                    col_info["code_list"] = {str(key): int(value) for key, value in value_counts.items()}

                schema["columns"].append(col_info)

            if ctx:
                await ctx.report_progress(100, 100, "Analysis complete")

            return schema

        except Exception as exc:
            if ctx:
                await ctx.error(f"Analysis failed: {str(exc)}")
            return {
                "success": False,
                "error": str(exc),
                "file_path": file_path,
            }

    async def analyze_folder(
        self,
        folder_path: str,
        recursive: bool = False,
        max_files: int = 50,
        ctx: Any = None,
    ) -> Dict[str, Any]:
        try:
            folder_path = os.path.normpath(folder_path)

            if not os.path.exists(folder_path):
                return {
                    "success": False,
                    "error": "Directory not found",
                    "folder_path": folder_path,
                }

            sas_files = self._find_sas_files(folder_path, recursive, max_files)

            if ctx:
                await ctx.info(f"Found {len(sas_files)} SAS files to process")

            results = []
            successful = 0
            failed = 0

            for index, file_path in enumerate(sas_files):
                if ctx and sas_files:
                    progress = (index / len(sas_files)) * 100
                    await ctx.report_progress(progress, 100, f"Processing {index + 1}/{len(sas_files)}")

                try:
                    result = await self.analyze_file(file_path, ctx)
                    if result.get("success"):
                        successful += 1
                    else:
                        failed += 1
                    results.append(result)
                except Exception as exc:
                    failed += 1
                    results.append(
                        {
                            "success": False,
                            "error": str(exc),
                            "file_path": file_path,
                        }
                    )

            return {
                "success": True,
                "folder_path": folder_path,
                "successful_analyses": successful,
                "failed_analyses": failed,
                "results": results,
            }

        except Exception as exc:
            if ctx:
                await ctx.error(f"Folder analysis failed: {str(exc)}")
            return {
                "success": False,
                "error": str(exc),
                "folder_path": folder_path,
            }