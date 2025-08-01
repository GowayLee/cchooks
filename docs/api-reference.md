# cchooks API Reference

A comprehensive, type-safe Python library for developing Claude Code hooks with automatic hook type detection and specialized contexts for each hook lifecycle.

## Overview

The `cchooks` library provides a complete interface for creating Claude Code hooks - user-defined shell commands that execute at various points in Claude Code's lifecycle. The library supports 6 distinct hook types with specialized contexts and output handlers.

### Hook Types

1. **PreToolUse** - Runs before tool execution, can approve or block tools
2. **PostToolUse** - Runs after tool execution, can only provide feedback
3. **Notification** - Processes notifications, no decision control
4. **UserPromptSubmit** - Filters and enriches user prompts before processing
5. **Stop** - Controls Claude's stopping behavior
6. **SubagentStop** - Controls subagent stopping behavior
7. **PreCompact** - Runs before transcript compaction

## Main Entry Points

### `create_context()`

Factory function that automatically detects the hook type from JSON input and returns the appropriate specialized context.

```python
from cchooks import create_context

# Read from stdin automatically
context = create_context()

# Or use custom stdin
with open('input.json') as f:
    context = create_context(stdin=f)
```

**Parameters:**

- `stdin` (TextIO, optional): Input stream to read JSON from. Defaults to `sys.stdin`.

**Returns:**

- `HookContext`: One of the 7 specialized context types based on `hook_event_name` in input.

**Raises:**

- `ParseError`: If JSON is invalid or not an object
- `InvalidHookTypeError`: If `hook_event_name` is not recognized
- `HookValidationError`: If required fields are missing

## Base Classes

### `BaseHookContext`

Abstract base class for all hook contexts. Provides common functionality and properties.

```python
from cchooks.contexts.base import BaseHookContext

class MyCustomContext(BaseHookContext):
    @property
    def output(self) -> "BaseHookOutput":
        return MyCustomOutput()
```

**Properties:**

- `session_id: str` - Unique session identifier
- `transcript_path: str` - Path to transcript file
- `hook_event_name: str` - Type of hook event
- `output: BaseHookOutput` - Output handler for this context type

**Methods:**

- `from_stdin(stdin: TextIO = sys.stdin) -> BaseHookContext` - Create context from stdin JSON

### `BaseHookOutput`

Abstract base class for all hook outputs. Provides common output methods and utilities.

**Methods:**

- `_continue_flow(suppress_output: bool = False) -> dict` - JSON response to continue processing
- `_stop_flow(stop_reason: str, suppress_output: bool = False) -> dict` - JSON response to stop processing
- `_with_specific_output(common_output: CommonOutput, hook_event_name: str, **specific_fields: Any)` - Add hook-specific outpout to common JSON structure
- `_success(message: Optional[str] = None) -> NoReturn` - Exit with success (code 0)
- `_error(message: str, exit_code: int = 1) -> NoReturn` - Exit with non-blocking error (code 1)
- `_block(reason: str) -> NoReturn` - Exit with blocking error (code 2)

## Hook Contexts

### `PreToolUseContext`

Runs before tool execution with the ability to approve or block tools.

```python
from cchooks import create_context
from cchooks.contexts import PreToolUseContext

context = create_context()
if isinstance(context, PreToolUseContext):
    tool_name = context.tool_name
    tool_input = context.tool_input

    if tool_name == "Write" and "password" in tool_input.get("file_path", ""):
        context.output.deny("Refusing to write to password file")
    else:
        context.output.allow()
```

**Properties:**

- `tool_name: ToolName` - Name of the tool being executed
- `tool_input: Dict[str, Any]` - Parameters being passed to the tool

**Output Methods:**

- `allow(reason: str = "", suppress_output: bool = False)` - Allow tool execution, show user the reason for allowing
- `deny(reason: str, suppress_output: bool = False)` - Deny tool execution, prompt Claude with the reason for denying
- `ask(suppress_output: bool = False)` - Ask user for permission
- `halt(reason: str, suppress_output: bool = False)` - Stop all processing immediately
- `exit_success(message: Optional[str] = None) -> NoReturn` - Exit 0 (success)
- `exit_non_block(message: str) -> NoReturn` - Exit 1 (non-blocking error)
- `exit_block(reason: str) -> NoReturn` - Exit 2 (blocking error)

### `PostToolUseContext`

Runs after tool execution to provide feedback or block processing.

```python
from cchooks.contexts import PostToolUseContext

if isinstance(context, PostToolUseContext):
    tool_name = context.tool_name
    tool_input = context.tool_input
    tool_response = context.tool_response

    if tool_response.get("success") == False:
        context.output.simple_block("Tool execution failed")
```

**Properties:**

- `tool_name: ToolName` - Name of the executed tool
- `tool_input: Dict[str, Any]` - Parameters that were passed to the tool
- `tool_response: Dict[str, Any]` - Response data from the tool execution

**Output Methods:**

- `accept(suppress_output: bool = False)` - Accept tool results
- `challenge(reason: str, suppress_output: bool = False)` - Challenge tool results
- `ignore(suppress_output: bool = False)` - Ignore tool results
- `halt(reason: str, suppress_output: bool = False)` - Stop all processing immediately
- `exit_success(message: Optional[str] = None) -> NoReturn` - Exit 0 (success)
- `exit_non_block(message: str) -> NoReturn` - Exit 1 (non-blocking error)
- `exit_block(reason: str) -> NoReturn` - Exit 2 (blocking error)

### `NotificationContext`

Processes notifications without decision control capabilities.

```python
from cchooks.contexts import NotificationContext

if isinstance(context, NotificationContext):
    message = context.message
    log_notification(message)
    context.output.acknowledge("Notification processed")
```

**Properties:**

- `message: str` - Notification message content

**Output Methods:**

- `acknowledge(message: Optional[str]) -> NoReturn` - Acknowledge and process information
- `exit_success(message: Optional[str]) -> NoReturn` - Exit 0 (success)
- `exit_non_block(message: str) -> NoReturn` - Exit 1 (non-blocking error)
- `exit_block(message: str) -> NoReturn` - Exit 2 (blocking error)

> `exit_block` and `exit_non_block` behavior of `Notification Hook` and `PreCompact Hook` is actually the same. All of them show `reason` or `message` to the user and Claude will keep going. And `exit_success` will show `message` in transcript (default hidden to the user). For details see [official docs](https://docs.anthropic.com/en/docs/claude-code/hooks#simple%3A-exit-code)

### `UserPromptSubmitContext`

Runs when the user submits a prompt, before Claude processes it. This allows you to add additional context based on the prompt/conversation, validate prompts, or block certain types of prompts.

```python
from cchooks.contexts import UserPromptSubmitContext

if isinstance(context, UserPromptSubmitContext):
    prompt = context.prompt

    # Block prompts with sensitive data
    if "password" in prompt.lower():
        context.output.block("Security: Prompt contains sensitive data")
    else:
        # Allow prompt to proceed
        context.output.allow()
```

**Properties:**

- `prompt: str` - The user-submitted prompt text

**Output Methods:**

- `allow(suppress_output: bool = False)` - Allow the prompt to proceed normally
- `block(reason: str, suppress_output: bool = False)` - Deny the prompt from being processed
- `add_context(reason: str, context: str, suppress_output: bool = False)` - Add additional context to the prompt.
- `halt(reason: str, suppress_output: bool = False)` - Stop all processing immediately
- `exit_success(message: Optional[str] = None) -> NoReturn` - Exit 0 (success)
- `exit_non_block(message: str) -> NoReturn` - Exit 1 (non-blocking error)
- `exit_block(reason: str) -> NoReturn` - Exit 2 (blocking error)

### `StopContext`

Controls Claude's stopping behavior when Claude wants to stop.

```python
from cchooks.contexts import StopContext

if isinstance(context, StopContext):
    if context.stop_hook_active:
        # Already handled by stop hook
        context.output.allow()
    else:
        # Allow Claude to stop
        context.output.allow()
```

**Properties:**

- `stop_hook_active: bool` - Whether stop hook is already active

**Output Methods:**

- `allow(suppress_output: bool = False)` - Allow Claude to stop
- `prevent(reason: str, suppress_output: bool = False)` - Prevent Claude from stopping
- `halt(reason: str, suppress_output: bool = False)` - Stop all processing immediately
- `exit_success(message: Optional[str] = None) -> NoReturn` - Exit 0 (success)
- `exit_non_block(message: str) -> NoReturn` - Exit 1 (non-blocking error)
- `exit_block(reason: str) -> NoReturn` - Exit 2 (blocking error)

### `SubagentStopContext`

Controls subagent stopping behavior when subagent wants to stop.

```python
from cchooks.contexts import SubagentStopContext

if isinstance(context, SubagentStopContext):
    # Similar to StopContext but for subagents
    context.output.allow()
```

**Properties:**

- `stop_hook_active: bool` - Whether stop hook is already active

**Output Methods:**
Same as `StopOutput`.

### `PreCompactContext`

Runs before transcript compaction with custom instructions.

```python
from cchooks.contexts import PreCompactContext

if isinstance(context, PreCompactContext):
    trigger = context.trigger  # "manual" or "auto"
    instructions = context.custom_instructions

    if trigger == "manual" and instructions:
        process_custom_instructions(instructions)

    context.output.acknowledge("Compaction ready")
```

**Properties:**

- `trigger: PreCompactTrigger` - Type of compaction trigger (`"manual"` or `"auto"`)
- `custom_instructions: str` - Custom instructions provided by user

**Output Methods:**

- `acknowledge(message: Optional[str]) -> NoReturn` - Acknowledge the compaction
- `exit_success(message: Optional[str]) -> NoReturn` - Exit 0 (success)
- `exit_non_block(message: str) -> NoReturn` - Exit 1 (non-blocking error)
- `exit_block(message: str) -> NoReturn` - Exit 2 (blocking error)

## Type Definitions

### Hook Event Types

```python
from cchooks.types import HookEventType

# Possible values:
HookEventType = Literal[
    "PreToolUse", "PostToolUse", "Notification",
    "UserPromptSubmit", "Stop", "SubagentStop", "PreCompact"
]
```

### Tool Names

```python
from cchooks.types import ToolName

# Possible values:
ToolName = Literal[
    "Task", "Bash", "Glob", "Grep", "Read",
    "Edit", "MultiEdit", "Write", "WebFetch", "WebSearch"
]
```

### Decision Types

```python
from cchooks.types import PreToolUseDecision, PostToolUseDecision, StopDecision, UserPromptSubmitDecision

# Possible values:
PreToolUseDecision = Literal["allow", "deny", "ask"]
PostToolUseDecision = Literal["block"]
StopDecision = Literal["block"]
UserPromptSubmitDecision = Literal["block"]
```

### Trigger Types

```python
from cchooks.types import PreCompactTrigger

# Possible values:
PreCompactTrigger = Literal["manual", "auto"]
```

## Exception Classes

### `CCHooksError`

Base exception for all cchooks errors.

### `HookValidationError`

Raised when hook input validation fails.

```python
try:
    context = create_context()
except HookValidationError as e:
    print(f"Validation error: {e}")
    sys.exit(1)
```

### `ParseError`

Raised when JSON parsing fails.

### `InvalidHookTypeError`

Raised when an invalid hook type is encountered.

## Standalone Output Utilities

Direct control over output and exit behavior when context objects are not available:

### `exit_success(message: Optional[str] = None, file: TextIO = sys.stdout) -> NoReturn`

Exit with success (exit code 0).

```python
from cchooks import exit_success

exit_success("Operation completed successfully")
```

### `exit_non_block(message: str, exit_code: int = 1, file: TextIO = sys.stderr) -> NoReturn`

Exit with error (non-blocking).

```python
from cchooks import exit_non_block

exit_non_block("Configuration error", exit_code=1)
```

### `exit_block(reason: str, file: TextIO = sys.stderr) -> NoReturn`

Exit with blocking error (exit code 2).

```python
from cchooks import exit_block

exit_block("Security violation detected")
```

### `output_json(data: Dict[str, Any], file: TextIO = sys.stdout) -> None`

Output JSON data to the specified file.

```python
from cchooks import output_json

output_json({"status": "success", "message": "Operation completed"})
```

### Error Handling Utilities

#### `safe_create_context(stdin: TextIO = sys.stdin, error_file: TextIO = sys.stderr) -> Any`

Safe wrapper around `create_context()` with built-in error handling. Exits gracefully on any error.

```python
from cchooks import safe_create_context, PreToolUseContext

context = safe_create_context()
assert isinstance(context, PreToolUseContext)
# Safe to proceed - any errors would have been handled
```

#### `handle_context_error(error: Exception, file: TextIO = sys.stderr) -> NoReturn`

Unified handler for all context creation errors.

```python
from cchooks import create_context, handle_context_error

try:
    context = create_context()
except Exception as e:
    handle_context_error(e)  # Graceful exit with appropriate message
```

#### Error-specific Handlers

- `handle_parse_error(error: Exception, file: TextIO = sys.stderr) -> NoReturn`
- `handle_validation_error(error: Exception, file: TextIO = sys.stderr) -> NoReturn`
- `handle_invalid_hook_type(error: Exception, file: TextIO = sys.stderr) -> NoReturn`

## Utility Functions

### `read_json_from_stdin(stdin: TextIO = sys.stdin) -> Dict[str, Any]`

Read and parse JSON from stdin with validation.

```python
from cchooks.utils import read_json_from_stdin

data = read_json_from_stdin()
print(f"Hook type: {data['hook_event_name']}")
```

### `validate_required_fields(data: Dict[str, Any], required_fields: list[str]) -> None`

Validate that required fields are present in the data.

```python
from cchooks.utils import validate_required_fields

data = {"name": "test", "value": 42}
validate_required_fields(data, ["name", "value"])  # OK
validate_required_fields(data, ["name", "missing"])  # Raises KeyError
```

### Safe Type Accessors

- `safe_get_str(data: Dict[str, Any], key: str, default: str = "") -> str`
- `safe_get_bool(data: Dict[str, Any], key: str, default: bool = False) -> bool`
- `safe_get_dict(data: Dict[str, Any], key: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]`

## Usage Examples

### Basic Hook Structure

```python
#!/usr/bin/env python3
"""Example hook for blocking dangerous file writes."""

import sys
from cchooks import create_context
from cchooks.contexts import PreToolUseContext

def main():
    try:
        context = create_context()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(context, PreToolUseContext):
        # Check for dangerous file operations
        if (context.tool_name == "Write" and
            "config/" in context.tool_input.get("file_path", "")):
            context.output.exit_block("Config files are protected")
        else:
            context.output.exit_success()

if __name__ == "__main__":
    main()
```

### JSON Output Mode

```python
#!/usr/bin/env python3
"""Example using JSON output for advanced control."""

from cchooks import create_context
from cchooks.contexts import PreToolUseContext

def main():
    context = create_context()

    if isinstance(context, PreToolUseContext):
        tool_name = context.tool_name
        tool_input = context.tool_input

        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if "rm -rf /" in command:
                context.output.block("Dangerous command detected")
            else:
                context.output.approve("Command looks safe")

if __name__ == "__main__":
    main()
```

### Post-Processing Hook

```python
#!/usr/bin/env python3
"""Example post-tool use hook for logging."""

import json
from cchooks import create_context
from cchooks.contexts import PostToolUseContext

def main():
    context = create_context()

    if isinstance(context, PostToolUseContext):
        # Log tool usage
        log_entry = {
            "tool": context.tool_name,
            "input": context.tool_input,
            "response": context.tool_response
        }

        with open("tool_usage.log", "a") as f:
            json.dump(log_entry, f)
            f.write("\n")

        context.output.exit_success("Logged successfully")

if __name__ == "__main__":
    main()
```

### Notification Handler

```python
#!/usr/bin/env python3
"""Example notification handler."""

from cchooks import create_context
from cchooks.contexts import NotificationContext

def main():
    context = create_context()

    if isinstance(context, NotificationContext):
        message = context.message

        # Some logic to send Desktop Notification

        context.output.acknowledge("Desktop Notification Sent!")

if __name__ == "__main__":
    main()
```

## Best Practices

1. **Always handle exceptions** - Use try-except blocks around `create_context()`
2. **Use type checking** - Use `isinstance()` to determine context type
3. **Choose appropriate output methods** - JSON output for complex decisions, simple exit codes for basic operations
4. **Provide clear messages** - Give meaningful reasons for blocking operations
5. **Test thoroughly** - Test with different hook types and edge cases
6. **Document your hooks** - Include clear documentation about what your hook does

## Package Structure

```
cchooks/
├── __init__.py           # Main exports
├── types.py             # Type definitions
├── exceptions.py        # Exception classes
├── utils.py            # Utility functions
└── contexts/           # Hook contexts
    ├── __init__.py
    ├── base.py         # Base classes
    ├── pre_tool_use.py
    ├── post_tool_use.py
    ├── notification.py
    ├── user_prompt_submit.py
    ├── stop.py
    ├── subagent_stop.py
    └── pre_compact.py
```

## Quick Reference

| Hook Type        | Can Block? | Decision Control | Key Properties                       |
| ---------------- | ---------- | ---------------- | ------------------------------------ |
| PreToolUse       | ✅         | approve/block    | tool_name, tool_input                |
| PostToolUse      | ✅         | block only       | tool_name, tool_input, tool_response |
| Notification     | ❌         | none             | message                              |
| UserPromptSubmit | ✅         | block only       | prompt                               |
| Stop             | ✅         | block only       | stop_hook_active                     |
| SubagentStop     | ✅         | block only       | stop_hook_active                     |
| PreCompact       | ❌         | none             | trigger, custom_instructions         |
