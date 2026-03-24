#!/usr/bin/env python3
"""Branch protection using cchooks SDK.

Blocks push to main/master and force-push on all branches.
Install: Add to PreToolUse hooks matching "Bash" in settings.json.
"""
import re
from cchooks import create_context
from cchooks.contexts import PreToolUseContext

ctx = create_context()
if isinstance(ctx, PreToolUseContext):
    cmd = ctx.tool_input.get("command", "")

    if re.search(r'\bgit\s+push\b.*\b(main|master)\b', cmd, re.I):
        ctx.output.block(reason="Direct push to main/master branch")
    elif re.search(r'\bgit\s+push\s+.*--force\b', cmd, re.I):
        ctx.output.block(reason="Force push overwrites remote history")
    elif re.search(r'\bgit\s+push\s+.*-f\b', cmd, re.I):
        ctx.output.block(reason="Force push (-f shorthand)")
