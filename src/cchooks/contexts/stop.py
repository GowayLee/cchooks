"""Stop hook context and output."""

import json
import sys
from typing import Any, Dict, NoReturn, Optional

from .base import BaseHookContext, BaseHookOutput
from ..exceptions import HookValidationError


class StopContext(BaseHookContext):
    """Context for Stop hooks."""

    def __init__(self, input_data: Dict[str, Any]) -> None:
        """Initialize Stop context."""
        super().__init__(input_data)
        self._validate_stop_fields()

    def _validate_stop_fields(self) -> None:
        """Validate Stop-specific fields."""
        if "stop_hook_active" not in self._input_data:
            self._missing_fields.append("stop_hook_active")

        if self._missing_fields:
            raise HookValidationError(
                f"Missing required Stop fields: {', '.join(self._missing_fields)}"
            )

    @property
    def stop_hook_active(self) -> bool:
        """stop_hook_active is true when Claude Code is already continuing as a result of a stop hook"""
        return bool(self._input_data["stop_hook_active"])

    @property
    def output(self) -> "StopOutput":
        """Get the Stop-specific output handler."""
        return StopOutput()


class StopOutput(BaseHookOutput):
    """Output handler for Stop hooks."""

    def halt(self, stop_reason: str, suppress_output: bool = False) -> None:
        """Stop all processing immediately with JSON response.

        Args:
            stop_reason (str): Stopping reason shown to the user, not shown to Claude
            suppress_output (bool): Hide stdout from transcript mode (default: False)
        """
        output = self._stop_flow(stop_reason, suppress_output)
        print(json.dumps(output), file=sys.stdout)

    def prevent(self, reason: str, suppress_output: bool = False) -> None:
        """Prevent Claude from stopping and Prompt Claude with JSON response.

        Args:
            reason (str): Reason shown to Clade for further reasoning
            suppress_output (bool): Hide stdout from transcript mode (default: False)
        """
        output = self._continue_flow(suppress_output)
        output.update({"decision": "block", "reason": reason})
        print(json.dumps(output), file=sys.stdout)

    def allow(self, suppress_output: bool = False) -> None:
        """Allow Claude to stop and Do nothing with JSON response.

        Args:
            suppress_output (bool): Hide stdout from transcript mode (default: False)
        """
        output = self._continue_flow(suppress_output)
        print(json.dumps(output), file=sys.stdout)

    def exit_success(self, message: Optional[str] = None) -> NoReturn:
        """Exit with success (exit code 0).

        Args:
            message (Optional[str]): Message shown to the user in transcript (default: None)
        """
        self._success(message)

    def exit_block(self, reason: str) -> NoReturn:
        """Exit with blocking error (exit code 2).

        Args:
            reason (str): Reason shown to Claude for further reasoning
        """
        self._block(reason)

    def exit_non_block(self, message: str) -> NoReturn:
        """Exit with non-blocking error (exit code 1).

        Args:
            message (str): Message shown to the user
        """
        self._error(message)
