#!/usr/bin/env python3
"""Block destructive commands (rm -rf, git reset --hard, git clean).

Usage in settings.json:
{
    "hooks": {
        "PreToolUse": [{
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "python3 /path/to/block_destructive.py"}]
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

# Block rm -rf on sensitive paths
if re.search(r'rm\s+(-[rf]+\s+)*(\/|~|\.\.\/)', command):
    ctx.block("rm on sensitive path detected. Target specific directories instead.")

# Block git reset --hard
if re.search(r'(^|;|&&)\s*git\s+reset\s+--hard', command):
    ctx.block("git reset --hard discards all uncommitted changes. Use git stash first.")

# Block git clean -fd
if re.search(r'(^|;|&&)\s*git\s+clean\s+-[a-z]*[fd]', command):
    ctx.block("git clean removes untracked files permanently. Use git clean -n to preview.")

# Block force push
if re.search(r'git\s+push\s+.*(-f\b|--force\b)', command):
    ctx.block("Force push destroys remote history. Use --force-with-lease for safer option.")

# Block push to main/master
if re.search(r'git\s+push\s+.*\b(main|master)\b', command):
    ctx.block("Push to protected branch. Push to a feature branch and create a PR.")

ctx.allow()
