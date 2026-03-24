#!/usr/bin/env python3
"""Block staging secret files (git add .env, credentials).

Usage in settings.json:
{
    "hooks": {
        "PreToolUse": [{
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "python3 /path/to/block_secrets.py"}]
        }]
    }
}
"""

import re
from cchooks import create_context, PreToolUseContext

ctx = create_context()

if not isinstance(ctx, PreToolUseContext):
    ctx.allow()

command = ctx.tool_input.get("command", "")
if not command:
    ctx.allow()

# Only check git add commands
if not re.search(r'^\s*git\s+add', command):
    ctx.allow()

# Block .env files
if re.search(r'git\s+add\s+.*\.env(\s|$|\.)', command, re.IGNORECASE):
    ctx.block(".env file contains secrets. Add to .gitignore instead.")

# Block credential/key files
if re.search(r'git\s+add\s+.*(credentials|\.pem|\.key|\.p12|id_rsa|id_ed25519)', command, re.IGNORECASE):
    ctx.block("Credential/key file should never be committed. Add to .gitignore.")

ctx.allow()
