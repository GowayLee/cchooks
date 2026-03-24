#!/usr/bin/env python3
"""Destructive command guard using cchooks SDK.

Blocks rm -rf /, git reset --hard, and similar destructive commands.
Install: Add to PreToolUse hooks matching "Bash" in settings.json.

Born from: https://github.com/anthropics/claude-code/issues/36339
  (User lost entire C:\Users directory to rm -rf via NTFS junctions)
"""
import re
from cchooks import create_context
from cchooks.contexts import PreToolUseContext

DANGEROUS = [
    re.compile(r'\brm\s+.*-rf\s+(/|~/?\s*$|\.\./)', re.I),
    re.compile(r'\bgit\s+reset\s+--hard', re.I),
    re.compile(r'\bgit\s+clean\s+-[a-zA-Z]*f', re.I),
    re.compile(r'\bchmod\s+(-R\s+)?777\s+/', re.I),
    re.compile(r'\bfind\s+/\s+-delete', re.I),
    re.compile(r'Remove-Item.*-Recurse.*-Force', re.I),
    re.compile(r'--no-preserve-root', re.I),
]

ctx = create_context()
if isinstance(ctx, PreToolUseContext):
    cmd = ctx.tool_input.get("command", "")
    if cmd and not cmd.lstrip().startswith(("echo ", "printf ")):
        for pattern in DANGEROUS:
            if pattern.search(cmd):
                ctx.output.block(reason=f"Destructive command: {cmd[:80]}")
                break
