# Examples

Ready-to-use hooks built with cchooks.

## Safety Hooks

| Hook | What It Blocks |
|------|---------------|
| [block_destructive.py](block_destructive.py) | rm -rf /, git reset --hard, force push, push to main |
| [block_secrets.py](block_secrets.py) | git add .env, credential files |

## Usage

1. Copy the hook to your hooks directory
2. Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "python3 /path/to/block_destructive.py"}]
    }]
  }
}
```

3. Restart Claude Code
