"""Portable sas-schema CLI bundled with the skill."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


_SAS_FILE_GLOB = "*.sas7bdat"
_SAS_FILE_EXT = ".sas7bdat"


def _write_json(data: dict, output_path: Path, indent: int) -> None:
    output_path.write_text(json.dumps(data, indent=indent, default=str), encoding="utf-8")


def _print_json(data: dict, indent: int) -> None:
    print(json.dumps(data, indent=indent, default=str))


def _create_analyzer(*, threshold: float = 0.15, debug: bool = False):
    try:
        from .core import SasSchemaAnalyzer
    except ModuleNotFoundError as exc:
        missing = exc.name or "required dependency"
        raise SystemExit(
            "Portable sas-schema dependencies are missing "
            f"({missing}). Install the packages listed in scripts/requirements.txt "
            "before running analyze."
        ) from exc

    return SasSchemaAnalyzer(code_list_threshold=threshold, debug=debug)


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


async def _analyze_single(args) -> int:
    analyzer = _create_analyzer(threshold=args.threshold, debug=args.debug)
    result = await analyzer.analyze_file(args.path, None)

    if args.output:
        _write_json(result, Path(args.output), args.indent)
        print(f"Schema written to: {args.output}", file=sys.stderr)
    else:
        _print_json(result, args.indent)

    return 0 if result.get("success") else 1


async def _analyze_batch(args) -> int:
    analyzer = _create_analyzer(threshold=args.threshold, debug=args.debug)
    result = await analyzer.analyze_folder(
        folder_path=args.path,
        recursive=args.recursive,
        max_files=args.max_files,
        ctx=None,
    )

    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

    written = 0
    for file_result in result.get("results", []):
        file_path = Path(file_result.get("file_path", ""))
        if not file_path.name:
            continue
        out_path = file_path.with_suffix(".json")
        _write_json(file_result, out_path, args.indent)
        written += 1

    successful = result.get("successful_analyses", 0)
    failed = result.get("failed_analyses", 0)
    print(
        f"Batch complete: {successful} succeeded, {failed} failed. "
        f"{written} JSON files written.",
        file=sys.stderr,
    )
    _print_json(
        {
            "success": True,
            "folder_path": result.get("folder_path"),
            "successful_analyses": successful,
            "failed_analyses": failed,
            "json_files_written": written,
        },
        args.indent,
    )

    return 0 if failed == 0 else 1


def _cmd_analyze(args) -> int:
    path = Path(args.path)
    if path.is_dir() or args.batch:
        return asyncio.run(_analyze_batch(args))
    return asyncio.run(_analyze_single(args))


def _list_files(args) -> int:
    directory = os.path.normpath(args.directory)
    if not os.path.exists(directory):
        _print_json(
            {
                "success": False,
                "error": "Directory not found",
                "directory": directory,
            },
            args.indent,
        )
        return 1

    files = []
    for file_path in _find_sas_files(directory, args.recursive):
        try:
            stat = os.stat(file_path)
            files.append({"file_path": file_path, "size_bytes": stat.st_size})
        except OSError:
            files.append({"file_path": file_path, "error": "Could not access file"})

    _print_json(
        {
            "success": True,
            "directory": directory,
            "files_found": len(files),
            "files": files,
        },
        args.indent,
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sas-schema",
        description="Extract SAS7BDAT schema as JSON",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="JSON indent level (default: 2)",
    )

    sub = parser.add_subparsers(dest="command")

    p_analyze = sub.add_parser("analyze", help="Analyze one SAS file or a folder of SAS files")
    p_analyze.add_argument("path", help="Path to a .sas7bdat file or a directory")
    p_analyze.add_argument(
        "--batch",
        action="store_true",
        help="Treat path as a folder even if it has a .sas7bdat extension",
    )
    p_analyze.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories (batch mode only)",
    )
    p_analyze.add_argument(
        "--max-files",
        type=int,
        default=50,
        metavar="N",
        help="Max files to process in batch mode (default: 50)",
    )
    p_analyze.add_argument(
        "--threshold",
        type=float,
        default=0.15,
        metavar="F",
        help="Code list detection threshold 0.0-1.0 (default: 0.15)",
    )
    p_analyze.add_argument(
        "--output",
        metavar="FILE",
        help="Single-file mode: write JSON to this file instead of stdout",
    )
    p_analyze.add_argument("--debug", action="store_true", help="Enable verbose logging")
    p_analyze.set_defaults(func=_cmd_analyze)

    p_list = sub.add_parser("list", help="Discover SAS7BDAT files in a directory")
    p_list.add_argument("directory", help="Directory to search")
    p_list.add_argument("--recursive", action="store_true", help="Recurse into subdirectories")
    p_list.set_defaults(func=_list_files, indent=2)
    p_list.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="JSON indent level (default: 2)",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help(sys.stderr)
        sys.exit(2)
    sys.exit(args.func(args))