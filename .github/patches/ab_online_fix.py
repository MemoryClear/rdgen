#!/usr/bin/env python3
"""
ab_online_fix.py

Fixes address book online status loss for Personal=1 mode.

Problem: Ab.pullAbImpl replaces the peers list with API data that has no online
field (Peer.fromJson sets online=false by default), causing the UI to briefly show
all peers as offline after a connect event triggers changePersonalHashPassword ->
pullAb(quiet:true).

Fix:  Before  peers.value = tmpPeers  save old online IDs, after restore them.
This is consistent with LegacyAb._deserialize which already has this fix.
"""

import os
import sys

TARGET = "flutter/lib/models/ab_model.dart"
INSERT_BEFORE = "    peers.value = tmpPeers;"
BEFORE_LINES = """    // Preserve online status (fix: Personal=1 causes brief offline after connect)
    final oldOnlineIDs = peers
        .where((e) => e.online)
        .map((e) => e.id)
        .toList();
"""
AFTER_LINES = """
    // Restore online status
    peers
        .where((e) => oldOnlineIDs.contains(e.id))
        .map((e) => e.online = true)
        .toList();
"""

def main():
    if not os.path.exists(TARGET):
        print(f"ERROR: {TARGET} not found", file=sys.stderr)
        sys.exit(1)

    with open(TARGET, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the target line
    idx = None
    for i, line in enumerate(lines):
        if line.rstrip() == INSERT_BEFORE:
            idx = i
            break

    if idx is None:
        print(f"ERROR: could not find '{INSERT_BEFORE}' in {TARGET}", file=sys.stderr)
        sys.exit(1)

    # Check already applied
    if idx >= 6 and lines[idx - 5].strip() == "// Preserve online status (fix: Personal=1 causes brief offline after connect)":
        print(f"{TARGET}: already patched, skipping")
        return

    # Insert before the target line
    new_lines = []
    new_lines.extend(BEFORE_LINES.splitlines(keepends=True))
    new_lines.append(lines[idx])  # keep the original peers.value = tmpPeers;
    new_lines.extend(AFTER_LINES.splitlines(keepends=True))

    result = lines[:idx] + new_lines + lines[idx + 1:]
    with open(TARGET, "w", encoding="utf-8") as f:
        f.writelines(result)

    print(f"{TARGET}: patched at line {idx + 1}")


if __name__ == "__main__":
    main()
