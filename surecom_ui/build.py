"""
Compile the shared Tailwind stylesheet for a consuming app.

Tailwind only emits the utility classes it actually finds in scanned files, so a
shared package cannot ship a useful pre-compiled stylesheet: it has no idea what
the consuming app's templates use. Instead each app runs this helper, which
scans both its own templates and this package's, and writes one stylesheet.

Deliberately does NOT import Django or touch settings, so it can run early in a
Docker build before any environment variables are available.

Usage:

    python -m surecom_ui.build --out static/css/app.css --source templates --minify

Set TAILWIND_BIN if the standalone Tailwind CLI is not on PATH as `tailwindcss`.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent
PACKAGE_CSS = PACKAGE_DIR / "static" / "surecom_ui" / "css" / "surecom-ui.css"
PACKAGE_TEMPLATES = PACKAGE_DIR / "templates"
# Shared sign-in pages (surecom_ui.auth). Scanned even when the app doesn't use
# them: a few unused utilities cost less than unstyled pages when it does.
AUTH_TEMPLATES = PACKAGE_DIR / "auth" / "templates"


def _as_css_path(path: pathlib.Path) -> str:
    """Tailwind reads these out of a CSS file, so backslashes must be escaped."""
    return str(path).replace("\\", "/")


def build_input_css(sources: list[pathlib.Path]) -> str:
    lines = [
        '@import "tailwindcss";',
        f'@import "{_as_css_path(PACKAGE_CSS)}";',
        "",
        "/* Scan this package's own templates for utilities used by shared components. */",
        f'@source "{_as_css_path(PACKAGE_TEMPLATES)}";',
        f'@source "{_as_css_path(AUTH_TEMPLATES)}";',
    ]
    if sources:
        lines.append("")
        lines.append("/* Scan the consuming app. */")
        for src in sources:
            lines.append(f'@source "{_as_css_path(src)}";')
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="surecom_ui.build")
    parser.add_argument("--out", required=True, help="Path to write the compiled CSS to.")
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        metavar="DIR",
        help="Directory of the consuming app to scan for classes. Repeatable.",
    )
    parser.add_argument("--minify", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument(
        "--print-input",
        action="store_true",
        help="Print the generated input CSS and exit without building.",
    )
    args = parser.parse_args(argv)

    if not PACKAGE_CSS.is_file():
        print(f"error: shared stylesheet missing at {PACKAGE_CSS}", file=sys.stderr)
        return 1

    sources = [pathlib.Path(s).resolve() for s in args.source]
    for src in sources:
        if not src.exists():
            print(f"warning: source path does not exist: {src}", file=sys.stderr)

    input_css = build_input_css(sources)

    if args.print_input:
        print(input_css, end="")
        return 0

    binary = os.environ.get("TAILWIND_BIN", "tailwindcss")
    if shutil.which(binary) is None:
        print(
            f"error: Tailwind CLI not found as {binary!r}.\n"
            "Install the standalone binary (no Node required) from\n"
            "https://github.com/tailwindlabs/tailwindcss/releases "
            "or set TAILWIND_BIN to its path.",
            file=sys.stderr,
        )
        return 1

    out = pathlib.Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    # Tailwind resolves relative @source paths against the CSS file, but every
    # path written above is absolute, so the temp file's location is irrelevant.
    with tempfile.TemporaryDirectory() as tmp:
        input_path = pathlib.Path(tmp) / "input.css"
        input_path.write_text(input_css, encoding="utf-8")

        cmd = [binary, "--input", str(input_path), "--output", str(out)]
        if args.minify:
            cmd.append("--minify")
        if args.watch:
            cmd.append("--watch")

        print(f"surecom-ui: building {out}")
        result = subprocess.run(cmd)

    if result.returncode != 0:
        print("error: Tailwind build failed", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
