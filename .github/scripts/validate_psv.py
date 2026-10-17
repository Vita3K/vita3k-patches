#!/usr/bin/env python3
"""Format checker for VitaCheat .psv files.

Usage: validate_psv.py [--warnings-as-errors] <file> [<file> ...]

Emits GitHub Actions workflow commands (::error / ::warning) so problems show up
as annotations on the pull request diff. Exits non-zero if any error was found.
"""

import argparse
import os
import re
import sys

REQUIRED_FIELDS = ("Title", "ID", "Region", "Version", "Type", "Code Author")

# PCSA00008.psv, PCSE00465-mp.psv, ...
FILENAME_RE = re.compile(r"^(PCS[A-Z]\d{5})(-[A-Za-z0-9_]+)?\.psv$")
META_RE = re.compile(r"^#\s*([^:]+?)\s*:\s*(.*?)\s*$")
# _V0 Cheat name / _V1 Cheat name
CHEAT_RE = re.compile(r"^_V[0-9]\S*(\s+.*)?$")
# $3002 81F254C0 00000014   (optional trailing comment)
CODE_RE = re.compile(r"^\$[0-9A-Fa-f]{4}\s+[0-9A-Fa-f]{8}\s+[0-9A-Fa-f]{8}\s*(#.*)?$")

errors = 0
warnings = 0


def report(level, path, line, message):
    global errors, warnings
    if level == "error":
        errors += 1
    else:
        warnings += 1
    where = f"file={path}" + (f",line={line}" if line else "")
    print(f"::{level} {where}::{message}")


def check(path):
    raw = open(path, "rb").read()

    name = os.path.basename(path)
    m = FILENAME_RE.match(name)
    if not m:
        report("error", path, 0,
               "File name must be <TitleID>.psv (e.g. PCSB00123.psv), "
               "optionally with a '-suffix'.")
    title_id = m.group(1) if m else None

    if raw.startswith(b"\xef\xbb\xbf"):
        report("warning", path, 1, "File starts with a UTF-8 BOM; save it without a BOM.")
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        report("error", path, 0, f"File is not valid UTF-8: {exc}")
        return
    if b"\r\n" in raw:
        report("warning", path, 1, "File uses CRLF line endings; LF is preferred.")
    if raw and not raw.endswith(b"\n"):
        report("warning", path, 0, "File does not end with a newline.")

    lines = text.replace("\r\n", "\n").split("\n")

    meta = {}
    seen_cheat = False
    code_lines = 0

    for no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("#"):
            # Metadata is only read from the header, before the first cheat.
            mm = META_RE.match(stripped)
            if mm and not seen_cheat:
                meta.setdefault(mm.group(1), (mm.group(2), no))
            continue

        if stripped.startswith("_V"):
            if not CHEAT_RE.match(stripped):
                report("error", path, no,
                       f"Malformed cheat header: {stripped!r} (expected '_V0 <name>').")
            elif len(stripped.split(None, 1)) < 2:
                report("warning", path, no, "Cheat header has no name.")
            seen_cheat = True
            continue

        if stripped.startswith("$"):
            code_lines += 1
            if not CODE_RE.match(stripped):
                report("error", path, no,
                       f"Malformed code line: {stripped!r} "
                       "(expected '$XXXX XXXXXXXX XXXXXXXX' in hex).")
            elif not seen_cheat:
                report("error", path, no, "Code line appears before any '_V0' cheat header.")
            continue

        report("error", path, no,
               f"Unrecognized line: {stripped!r} "
               "(lines must start with '#', '_V' or '$').")

    for field in REQUIRED_FIELDS:
        if field not in meta:
            report("error", path, 1, f"Missing metadata field: '# {field}: ...'")
        elif not meta[field][0]:
            report("warning", path, meta[field][1], f"Metadata field '{field}' is empty.")

    if title_id and "ID" in meta:
        listed = re.findall(r"PCS[A-Z]\d{5}", meta["ID"][0])
        if title_id not in listed:
            report("error", path, meta["ID"][1],
                   f"'# ID: {meta['ID'][0]}' does not contain the title ID "
                   f"from the file name ({title_id}).")

    if not seen_cheat:
        report("error", path, 0, "File contains no cheat ('_V0 ...') entry.")
    elif code_lines == 0:
        report("error", path, 0, "File contains no code ('$....') line.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--warnings-as-errors", action="store_true")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    if not args.files:
        print("No .psv files to check.")
        return 0

    for path in args.files:
        if not os.path.isfile(path):
            continue
        check(path)

    print(f"\nChecked {len(args.files)} file(s): {errors} error(s), {warnings} warning(s).")
    if errors or (warnings and args.warnings_as_errors):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
