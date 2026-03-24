#!/usr/bin/env python3
"""Secret leak prevention using cchooks SDK.

Blocks git add .env, credential files, and git add . when .env exists.
Install: Add to PreToolUse hooks matching "Bash" in settings.json.

Born from: https://github.com/anthropics/claude-code/issues/16561
  (API keys committed via git add .)
"""
import os
import re
from cchooks import create_context
from cchooks.contexts import PreToolUseContext

ctx = create_context()
if isinstance(ctx, PreToolUseContext):
    cmd = ctx.tool_input.get("command", "")

    # Block git add .env*
    if re.search(r'\bgit\s+add\s+.*\.env\b', cmd, re.I):
        ctx.output.block(reason="Adding .env file to git exposes secrets")

    # Block git add of credential files
    elif re.search(r'\bgit\s+add\s+.*(\.pem|\.key|id_rsa|credentials)', cmd, re.I):
        ctx.output.block(reason="Adding credential file to git")

    # Warn on git add . / git add -A (may include .env)
    elif re.search(r'\bgit\s+add\s+(-A|--all|\.)\s*$', cmd):
        if os.path.exists('.env') or os.path.exists('.env.local'):
            ctx.output.block(reason="git add all with .env present — use specific files")
