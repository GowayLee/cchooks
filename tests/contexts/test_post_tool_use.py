"""Tests for PostToolUseContext and PostToolUseOutput."""

import json
from io import StringIO
from unittest.mock import patch

import pytest

from cchooks.contexts.post_tool_use import PostToolUseContext
from cchooks.exceptions import HookValidationError


class TestPostToolUseContext:
    """Test PostToolUseContext functionality."""

    def test_valid_context_creation(self):
        """Test creating context with valid data."""
        data = {
            "hook_event_name": "PostToolUse",
            "session_id": "test-session-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "Hello World"},
            "tool_response": {"success": True, "content": "File written successfully"},
        }

        context = PostToolUseContext(data)

        assert context.hook_event_name == "PostToolUse"
        assert context.session_id == "test-session-123"
        assert context.transcript_path == "/tmp/transcript.json"
        assert context.tool_name == "Write"
        assert context.tool_input == {
            "file_path": "/tmp/test.txt",
            "content": "Hello World",
        }
        assert context.tool_response == {
            "success": True,
            "content": "File written successfully",
        }

    def test_context_with_error_response(self):
        """Test context creation with error response."""
        data = {
            "hook_event_name": "PostToolUse",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {"file_path": "/etc/protected.txt", "content": "attempt"},
            "tool_response": {"success": False, "error": "Permission denied"},
        }

        context = PostToolUseContext(data)
        assert context.tool_response["success"] is False
        assert context.tool_response["error"] == "Permission denied"

    def test_context_validation_missing_required_fields(self):
        """Test context validation with missing required fields."""
        invalid_cases = [
            (
                {},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "tool_name",
                    "tool_input",
                    "tool_response",
                ],
            ),
            (
                {"hook_event_name": "PostToolUse"},
                [
                    "session_id",
                    "transcript_path",
                    "tool_name",
                    "tool_input",
                    "tool_response",
                ],
            ),
            (
                {"tool_name": "Write"},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "tool_input",
                    "tool_response",
                ],
            ),
            (
                {"tool_input": {}},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "tool_name",
                    "tool_response",
                ],
            ),
            (
                {"tool_response": {}},
                [
                    "session_id",
                    "transcript_path",
                    "hook_event_name",
                    "tool_name",
                    "tool_input",
                ],
            ),
        ]

        for data, missing_fields in invalid_cases:
            with pytest.raises(HookValidationError) as exc_info:
                PostToolUseContext(data)

            error_msg = str(exc_info.value)
            for field in missing_fields:
                assert field in error_msg


class TestPostToolUseOutput:
    """Test PostToolUseOutput functionality."""

    def test_exit_success(self):
        """Test simple approve method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "test"},
            "tool_response": {"success": True, "content": "success"},
        }

        context = PostToolUseContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_success("Operation completed successfully")
            mock_exit.assert_called_once_with(0)

    def test_exit_block(self):
        """Test simple block method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "test"},
            "tool_response": {"success": False, "error": "Operation failed"},
        }

        context = PostToolUseContext(data)

        with patch("sys.exit") as mock_exit:
            context.output.exit_block("Post-processing detected issues")
            mock_exit.assert_called_once_with(2)

    def test_challenge(self):
        """Test continue block method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.py", "content": "print('hello')"},
            "tool_response": {"success": True, "content": "File written"},
        }

        context = PostToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.challenge("Python file written, consider formatting")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert result["decision"] == "block"
            assert result["reason"] == "Python file written, consider formatting"

    def test_halt(self):
        """Test stop processing method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "test"},
            "tool_response": {"success": False, "error": "Security violation"},
        }

        context = PostToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.halt("Security violation detected")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is False
            assert result["stopReason"] == "Security violation detected"

    def test_accept(self):
        """Test continue direct method."""
        data = {
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "test"},
            "tool_response": {"success": True, "content": "success"},
        }

        context = PostToolUseContext(data)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.accept()

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)

            assert result["continue"] is True
            assert "decision" not in result  # Should not include decision

    def test_output_suppression(self):
        """Test output suppression functionality."""
        data = {
            "hook_event_name": "PostToolUse",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.py", "content": "print('hello')"},
            "tool_response": {"success": True, "content": "File written"},
        }

        context = PostToolUseContext(data)

        # Test suppress_output=True
        context.output.accept(suppress_output=True)


class TestPostToolUseRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_auto_format_python_files(self):
        """Test auto-formatting Python files after write."""
        data = {
            "hook_event_name": "PostToolUse",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/project/src/utils.py",
                "content": "def test(): pass",
            },
            "tool_response": {"success": True, "content": "File written"},
        }

        context = PostToolUseContext(data)

        # Test that we can access file extension
        file_path = context.tool_input["file_path"]
        assert file_path.endswith(".py")

        # Test accept for auto-formatting
        context.output.accept(suppress_output=True)

    def test_log_operations(self):
        """Test logging operations after tool use."""
        operations = [
            ("Write", {"file_path": "/tmp/log.txt"}, "File written"),
            ("Bash", {"command": "mkdir /tmp/test"}, "Directory created"),
            ("Read", {"file_path": "/tmp/config.json"}, "Config read"),
        ]

        for tool_name, tool_input, expected_msg in operations:
            data = {
                "hook_event_name": "PostToolUse",
                "session_id": "test-123",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_response": {"success": True, "content": expected_msg},
            }

            context = PostToolUseContext(data)

            # Test that we can process the operation
            assert context.tool_name == tool_name
            assert context.tool_input == tool_input
            assert context.tool_response["success"] is True

    def test_error_notification(self):
        """Test processing error notifications."""
        data = {
            "hook_event_name": "PostToolUse",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {"file_path": "/protected/file.txt", "content": "test"},
            "tool_response": {
                "success": False,
                "error": "Permission denied: /protected/file.txt",
            },
        }

        context = PostToolUseContext(data)

        # Test that we can access error information
        assert context.tool_response["success"] is False
        assert "Permission denied" in context.tool_response["error"]

        # Test error handling
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            context.output.challenge("Write failed due to permissions")

            output = mock_stdout.getvalue().strip()
            result = json.loads(output)
            assert result["continue"] is True
            assert "permissions" in result["reason"]

    def test_cleanup_operations(self):
        """Test cleanup operations after tool use."""
        data = {
            "hook_event_name": "PostToolUse",
            "session_id": "test-123",
            "transcript_path": "/tmp/transcript.json",
            "cwd": "/home/user/project",
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/temp_file.txt", "content": "temporary"},
            "tool_response": {"success": True, "content": "Temporary file created"},
        }

        context = PostToolUseContext(data)

        # Test cleanup decision
        file_path = context.tool_input["file_path"]
        if "/tmp/" in file_path:
            context.output.accept(suppress_output=True)
            assert file_path.endswith(".txt")
