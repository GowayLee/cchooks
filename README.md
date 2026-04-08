<div align="center">

<h1>cchooks</h1>
<h3>Claude Code Hook SDK for Python</h3>

![Static Badge](https://img.shields.io/badge/claude--code-black?style=flat&logo=claude&logoColor=%23D97757&link=https%3A%2F%2Fgithub.com%2Fanthropics%2Fclaude-code)
[![Mentioned in Awesome Claude Code](https://awesome.re/mentioned-badge.svg)](https://github.com/hesreallyhim/awesome-claude-code)
[![Mentioned in awesome-claude-code-hooks](https://awesome.re/mentioned-badge.svg)](https://github.com/ithiria894/awesome-claude-code-hooks)
![GitHub Repo stars](https://img.shields.io/github/stars/gowaylee/cchooks)

![PyPI - Version](https://img.shields.io/pypi/v/cchooks)
![PyPI - Downloads](https://img.shields.io/pypi/dm/cchooks)
![PyPI - License](https://img.shields.io/pypi/l/cchooks)

</div>

---

A lightweight Python Toolkit that makes building Claude Code hooks as simple as writing a few lines of code. Stop worrying about JSON parsing and focus on what your hook should actually do.

> **New to Claude Code hooks?** Check the [official docs](https://docs.anthropic.com/en/docs/claude-code/hooks) for the big picture.

> **Need the full API?** See the [API Reference](docs/api-reference.md) for complete documentation.

## Features

- **One-liner setup**: `create_context()` handles all the boilerplate
- **Zero config**: Automatic JSON parsing and validation from stdin
- **Smart detection**: Automatically figures out which hook you're building
- **9 hook types**: Support for all Claude Code hook events including SessionStart and SessionEnd
- **Two modes**: Simple exit codes OR advanced JSON control
- **Type-safe**: Full type hints and IDE autocompletion
- **System Message Support**: Provide optional warning messages to users for all decision-making hooks

## Installation

```bash
pip install cchooks
# or
uv add cchooks
```

## Quick Start

Build a PreToolUse hook that blocks dangerous file writes:

```python
#!/usr/bin/env python3
from cchooks import create_context, PreToolUseContext

c = create_context()

# Determine hook type
assert isinstance(c, PreToolUseContext)

# Block writes to .env files
if c.tool_name == "Write" and ".env" in c.tool_input.get("file_path", ""):
    c.output.exit_deny("Nope! .env files are protected")
else:
    c.output.exit_success()
```

Save as `hooks/env-guard.py`, make executable:

```bash
chmod +x hooks/env-guard.py
```

That's it. No JSON parsing, no validation headaches.

## Brief Tutorial

Build each hook type with real examples:

### PreToolUse (Security Guard)

Block dangerous commands before they run:

```python
#!/usr/bin/env python3
from cchooks import create_context, PreToolUseContext

c = create_context()

assert isinstance(c, PreToolUseContext)
# Block rm -rf commands with user warning
if c.tool_name == "Bash" and "rm -rf" in c.tool_input.get("command", ""):
    c.output.deny(
        reason="You should not execute this command: System protection: rm -rf blocked",
        system_message="⚠️ This command could permanently delete files. Please use caution."
    )
else:
    c.output.allow()
```

### PostToolUse (Auto-formatter)

Format Python files after writing:

```python
#!/usr/bin/env python3
import subprocess
from cchooks import create_context, PostToolUseContext

c = create_context()

assert isinstance(c, PostToolUseContext)
if c.tool_name == "Write" and c.tool_input.get("file_path", "").endswith(".py"):
    file_path = c.tool_input["file_path"]
    subprocess.run(["black", file_path])
    print(f"Auto-formatted: {file_path}")
```

### Notification (Desktop Alerts)

Send desktop notifications:

```python
#!/usr/bin/env python3
import os
from cchooks import create_context, NotificationContext

c = create_context()

assert isinstance(c, NotificationContext)
if "permission" in c.message.lower():
    os.system(f'notify-send "Claude" "{c.message}"')
```

### Stop (Task Manager)

Keep Claude working on long tasks:

```python
#!/usr/bin/env python3
from cchooks import create_context, StopContext

c = create_context()

assert isinstance(c, StopContext)
if not c.stop_hook_active: # Claude has not been activated by other Stop Hook
    c.output.prevent(
        reason="Hey Claude, you should try to do more works!",
        system_message="Claude is working on important tasks. You can stop manually if needed."
    ) # Prevent from stopping, and prompt Claude
else:
    c.output.allow()  # Allow stop
```

> Since hooks are executed in parallel in Claude Code, it is necessary to check `stop_hook_active` to determine if Claude has already been activated by another parallel Stop Hook.

### SubagentStop (Workflow Control)

Same as Stop, but for subagents:

```python
from cchooks import create_context, SubagentStopContext
c = create_context()
assert isinstance(c, SubagentStopContext)
c.output.allow()  # Let subagents complete
```

### UserPromptSubmit (Prompt Filter)

Filter and enrich user prompts before processing:

```python
from cchooks import create_context, UserPromptSubmitContext

c = create_context()

assert isinstance(c, UserPromptSubmitContext)
# Block prompts with sensitive data with user warning
if "password" in c.prompt.lower():
    c.output.block(
        reason="Security: Prompt contains sensitive data",
        system_message="🔒 For security reasons, please avoid sharing passwords or sensitive information."
    )
else:
    c.output.allow()
```

### SessionStart (Context Loader)

Load development context when Claude Code starts or resumes:

```python
#!/usr/bin/env python3
import os
from cchooks import create_context, SessionStartContext

c = create_context()

assert isinstance(c, SessionStartContext)
if c.source == "startup":
    # Load project-specific context
    project_root = os.getcwd()
    if os.path.exists(f"{project_root}/.claude-context"):
        with open(f"{project_root}/.claude-context", "r") as f:
            context = f.read()
            print(f"Loaded project context:\n{context}")
elif c.source == "resume":
    print("Resuming previous session...")
elif c.source == "clear":
    print("Starting fresh session...")

# Always exit with success - output is added to session context
c.output.exit_success()
```

> **Note**: SessionStart hooks cannot block Claude processing. Any stdout output from exit code 0 is automatically added to the session context (not the transcript).

### SessionEnd (Cleanup Handler)

Perform cleanup tasks when Claude Code session ends:

```python
#!/usr/bin/env python3
import os
import json
from datetime import datetime
from cchooks import create_context, SessionEndContext

c = create_context()

assert isinstance(c, SessionEndContext)

# Log session end information
session_info = {
    "session_id": c.session_id,
    "end_time": datetime.now().isoformat(),
    "reason": c.reason,
    "transcript_path": c.transcript_path
}

# Save session summary
log_file = f"/tmp/claude-sessions.log"
with open(log_file, "a") as f:
    f.write(json.dumps(session_info) + "\n")

# Perform cleanup based on session end reason
if c.reason == "clear":
    # Clean up temporary files
    temp_dir = f"/tmp/claude-temp-{c.session_id}"
    if os.path.exists(temp_dir):
        os.system(f"rm -rf {temp_dir}")
        print(f"Cleaned up temporary directory: {temp_dir}")
elif c.reason == "logout":
    # Save user preferences or session state
    print(f"User logged out - session {c.session_id} ended")
elif c.reason == "prompt_input_exit":
    # Handle manual exit
    print(f"Manual exit - session {c.session_id} terminated")
else:
    # Other reasons
    print(f"Session {c.session_id} ended: {c.reason}")

# Always exit with success - cleanup completed
c.output.exit_success("Session cleanup completed")
```

> **Note**: SessionEnd hooks cannot block session termination since the session is already ending. They are ideal for cleanup tasks, logging, and saving state. Success output is logged to debug only, while errors are shown to users via stderr.

### PreCompact (Custom Instructions)

Add custom compaction rules:

```python
from cchooks import create_context, PreCompactContext

c = create_context()

assert isinstance(c, PreCompactContext)
if c.custom_instructions:
    print(f"Using custom compaction: {c.custom_instructions}")
```

## Standalone Output Utilities

### Direct Control

When you need direct control over output and exit behavior outside of context objects, use these standalone utilities:

```python
#!/usr/bin/env python3
from cchooks import exit_success, exit_block, exit_non_block, output_json

# Direct exit control
exit_success("Operation completed successfully")
exit_block("Security violation detected")
exit_non_block("Warning: something unexpected happened")

# JSON output
output_json({"status": "error", "reason": "invalid input"})
```

### Available Standalone Functions

- `exit_success(message=None)` - Exit with code 0 (success)
- `exit_non_block(message, exit_code=1)` - Exit with error code (non-blocking)
- `exit_block(reason)` - Exit with code 2 (blocking error)
- `output_json(data)` - Output JSON data to stdout
- `safe_create_context()` - Safe wrapper with built-in error handling
- `handle_context_error(error)` - Unified error handler for context creation

### Error Handling

Handle context creation errors gracefully with built-in utilities:

```python
#!/usr/bin/env python3
from cchooks import safe_create_context, PreToolUseContext

# Automatic error handling - exits gracefully on any error
context = safe_create_context()

# If we reach here, context creation succeeded
assert isinstance(context, PreToolUseContext)

# Your normal hook logic here...
```

Or use explicit error handling:

```python
#!/usr/bin/env python3
from cchooks import create_context, handle_context_error, PreToolUseContext

try:
    context = create_context()
except Exception as e:
    handle_context_error(e)  # Graceful exit with appropriate message

# Normal processing...
```

## Quick API Guide

| Hook Type            | What You Get                         | Key Properties               |
| -------------------- | ------------------------------------ | ---------------------------- |
| **PreToolUse**       | `c.tool_name`, `c.tool_input`        | Block dangerous tools        |
| **PostToolUse**      | `c.tool_response`                    | React to tool results        |
| **Notification**     | `c.message`                          | Handle notifications         |
| **Stop**             | `c.stop_hook_active`                 | Control when Claude stops    |
| **SubagentStop**     | `c.stop_hook_active`                 | Control subagent behavior    |
| **UserPromptSubmit** | `c.prompt`                           | Filter and enrich prompts    |
| **PreCompact**       | `c.trigger`, `c.custom_instructions` | Modify transcript compaction |
| **SessionStart**     | `c.source`                           | Load development context     |
| **SessionEnd**       | `c.reason`                           | Perform cleanup tasks        |

> **Note**: Most decision-making methods support the optional `system_message` parameter for providing user warnings. See the [System Message Support](#system-message-support) section for details.

## System Message Support

The `system_message` parameter allows you to provide optional warning messages that will be shown to users when your hooks make decisions. This is particularly useful for security hooks, policy enforcement, and providing contextual feedback.

### Supported Hook Types

The `system_message` parameter is available in the following hook types:

| Hook Type            | Supported Methods                                                |
| -------------------- | ---------------------------------------------------------------- |
| **PreToolUse**       | `allow()`, `deny()`, `ask()`, `halt()`                           |
| **PostToolUse**      | `accept()`, `challenge()`, `ignore()`, `add_context()`, `halt()` |
| **Stop**             | `halt()`, `prevent()`, `allow()`                                 |
| **SubagentStop**     | `halt()`, `prevent()`, `allow()`                                 |
| **UserPromptSubmit** | `allow()`, `block()`, `add_context()`, `halt()`                  |
| **SessionStart**     | `add_context()`                                                  |

### JSON Output Format

When you provide a `system_message`, it appears in the JSON output as the `systemMessage` field:

```json
{
  "continue": false,
  "decision": "deny",
  "reason": "Dangerous command detected",
  "systemMessage": "⚠️ This command could permanently delete files. Please use caution."
}
```

### Simple Mode (Exit Codes)

```python
# Exit 0 = success, Exit 1 = non-block, Exit 2 = deny/block
c.output.exit_success()  # ✅
c.output.exit_non_block("reason")  # ❌
c.output.exit_deny("reason")  # ❌
```

### Advanced Mode (JSON)

```python
# Precise control over Claude's behavior with user warnings
c.output.allow("reason", system_message="Optional warning message")
c.output.deny("reason", system_message="Security warning")
c.output.ask(system_message="This operation requires your attention")
```

## Production Examples

### Multi-tool Security Guard

Block dangerous operations across multiple tools:

```python
#!/usr/bin/env python3
from cchooks import create_context, PreToolUseContext

DANGEROUS_COMMANDS = {"rm -rf", "sudo", "format", "fdisk"}
SENSITIVE_FILES = {".env", "secrets.json", "id_rsa"}

c = create_context()

assert isinstance(c, PreToolUseContext)
# Block dangerous Bash commands
if c.tool_name == "Bash":
    command = c.tool_input.get("command", "")
    if any(danger in command for danger in DANGEROUS_COMMANDS):
        c.output.exit_block("Security: Dangerous command blocked")
    else:
        c.output.exit_success()

# Block writes to sensitive files
elif c.tool_name == "Write":
    file_path = c.tool_input.get("file_path", "")
    if any(sensitive in file_path for sensitive in SENSITIVE_FILES):
        c.output.exit_deny(f"Protected file: {file_path}")
    else:
        c.output.exit_success()

else:
    c.output.ask() # Pattern not matched, let Claude decide
```

### Auto-linter Hook

Lint Python files after writing:

```python
#!/usr/bin/env python3
import subprocess
from cchooks import create_context, PostToolUseContext

c = create_context()

assert isinstance(c, PostToolUseContext)
if c.tool_name == "Write" and c.tool_input.get("file_path", "").endswith(".py"):
    file_path = c.tool_input["file_path"]

    # Run ruff linter
    result = subprocess.run(["ruff", "check", file_path], capture_output=True)

    if result.returncode == 0:
        print(f"✅ {file_path} passed linting")
    else:
        print(f"⚠️  {file_path} has issues:")
        print(result.stdout.decode())

    c.output.exit_success()
```

### Git-aware Auto-commit

Auto-commit file changes:

```python
#!/usr/bin/env python3
import subprocess
from cchooks import create_context, PostToolUseContext

c = create_context()

assert isinstance(c, PostToolUseContext)
if c.tool_name == "Write":
    file_path = c.tool_input.get("file_path", "")

    # Skip non-git files
    if not file_path.startswith("/my-project/"):
        c.output.exit_success()

    # Auto-commit Python changes
    if file_path.endswith(".py"):
        try:
            subprocess.run(["git", "add", file_path], check=True)
            subprocess.run([
                "git", "commit", "-m",
                f"auto: update {file_path.split('/')[-1]}"
            ], check=True)
            print(f"📁 Committed: {file_path}")
        except subprocess.CalledProcessError:
            print("Git commit failed - probably no changes")

    c.output.exit_success()
```

### Permission Logger

Log all permission requests:

```python
#!/usr/bin/env python3
import json
import datetime
from cchooks import create_context, PreToolUseContext

c = create_context()

assert isinstance(c, PreToolUseContext)
if c.tool_name == "Write":
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file": c.tool_input.get("file_path"),
        "action": "write_requested"
    }

    with open("/tmp/permission-log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    c.output.exit_success()
```

## Development

```bash
git clone https://github.com/GowayLee/cchooks.git
cd cchooks
make help # See detailed dev commands
```

## License

MIT License - see LICENSE file for details.
