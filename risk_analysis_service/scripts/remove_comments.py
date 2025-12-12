import argparse
import os
import sys
import io
import tokenize
from typing import Iterable


EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "venv",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "dist",
    "build",
}


def iter_py_files(paths: Iterable[str]) -> Iterable[str]:
    for path in paths:
        if os.path.isfile(path) and path.endswith(".py"):
            yield os.path.abspath(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    if f.endswith(".py"):
                        yield os.path.abspath(os.path.join(root, f))


def remove_hash_comments(source_bytes: bytes) -> bytes:
    out_tokens = []
    try:
        tok_gen = tokenize.tokenize(io.BytesIO(source_bytes).readline)
        for tok in tok_gen:
            if tok.type == tokenize.COMMENT:
                continue
            out_tokens.append(tok)
        new_bytes = tokenize.untokenize(out_tokens)
        if isinstance(new_bytes, str):
            return new_bytes.encode("utf-8")
        return new_bytes
    except tokenize.TokenError:
        return source_bytes


def process_file(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            original = f.read()
        processed = remove_hash_comments(original)
        if processed != original:
            with open(path, "wb") as f:
                f.write(processed)
        return True
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="remove_comments",
        description="Remove hash (#) comments from Python files.",
    )
    parser.add_argument("targets", nargs="+")
    args = parser.parse_args()
    success = True
    for file_path in iter_py_files(args.targets):
        ok = process_file(file_path)
        if not ok:
            success = False
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
