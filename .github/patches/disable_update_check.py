#!/usr/bin/env python3
"""Neutralise RustDesk's software-update check in src/common.rs.

Replaces the body of `do_check_software_update()` with `return Ok(());`.

Why not sed: the old one-liner was
    sed -i '/let (request, url) =/,/Ok(())/{/Ok(())/!d}'
which relies on an `Ok(())` appearing inside the function. RustDesk master
(2026-10) rewrote that function so its body has no `Ok(())` until ~1100 lines
later, inside `key_exchange` - the sed then ate the rest of the file and the
build died with "unexpected closing delimiter".

This script:
  * finds the function by its signature,
  * replaces everything up to the first `}` in column 0 (top-level items in this
    file are not indented, so that is the function's closing brace),
  * refuses to act - non-zero exit - when the anchor is missing or the removed
    block is suspiciously large, so a silent no-op or a runaway delete shows up
    as a failed build instead of a mysterious compile error.
"""

import sys

SIGNATURE = "pub async fn do_check_software_update() -> hbb_common::ResultType<()> {"
BODY = "    return Ok(());\n"
MAX_BODY_LINES = 400  # the real body is ~40 lines; anything bigger means trouble


def fail(msg):
    print(f"::error::disable_update_check: {msg}")
    sys.exit(1)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "./src/common.rs"
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            lines = f.readlines()
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")

    hits = [i for i, line in enumerate(lines) if line.strip().startswith(SIGNATURE)]
    if len(hits) != 1:
        fail(f"expected exactly one {SIGNATURE!r} in {path}, found {len(hits)}")
    start = hits[0]

    end = None
    for i in range(start + 1, len(lines)):
        if lines[i].rstrip("\r\n") == "}":
            end = i
            break
    if end is None:
        fail(f"closing brace of do_check_software_update not found after line {start + 1}")

    removed = end - start - 1
    if removed > MAX_BODY_LINES:
        fail(
            f"refusing to delete {removed} lines between line {start + 1} and {end + 1}; "
            "the function layout changed, inspect src/common.rs"
        )
    if removed == 1 and lines[start + 1].strip() == "return Ok(());":
        print("::notice::disable_update_check: already neutralised, nothing to do")
        return

    body_removed = "".join(lines[start + 1 : end])
    if "update" not in body_removed.lower():
        fail(
            f"the block after {SIGNATURE!r} does not look like the update check "
            f"(checked lines {start + 2}-{end}); refusing to touch it"
        )

    new_lines = lines[: start + 1] + [BODY, "}\n"] + lines[end + 1 :]
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.writelines(new_lines)

    print(
        f"::notice::disable_update_check: replaced {removed} line(s) of "
        f"do_check_software_update with `return Ok(());` in {path}"
    )


if __name__ == "__main__":
    main()
