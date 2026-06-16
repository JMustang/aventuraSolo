#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from core.story_validator import StoryValidationResult, validate_all_stories, validate_story_file


def _print_result(result: StoryValidationResult) -> None:
    status = "OK" if result.ok else "ERRO"
    print(f"\n[{status}] {result.file}")

    for warning in result.warnings:
        print(f"  ⚠ {warning}")

    for error in result.errors:
        print(f"  ✗ {error}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida arquivos JSON de histórias antes de adicioná-los ao catálogo."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Caminho(s) para arquivo(s) .json. Se omitido, use --all.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Valida todas as histórias em data/stories/{tema}/.",
    )

    args = parser.parse_args()

    if args.all:
        results = validate_all_stories()
        if not results:
            print("Nenhuma história encontrada em data/stories/{tema}/.")
            return 1
    elif args.files:
        results = [validate_story_file(Path(file)) for file in args.files]
    else:
        parser.print_help()
        return 1

    for result in results:
        _print_result(result)

    total = len(results)
    failed = sum(1 for result in results if not result.ok)
    passed = total - failed

    print(f"\nResumo: {passed}/{total} arquivo(s) válido(s).")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
