"""Tests for tool parameter validation"""

import pytest

import sys
sys.path.insert(0, 'src')

from pycode.tool_validation import (
    ToolParameterValidator,
    validate_tool_parameters,
    register_standard_schemas,
    ToolValidationError,
)


class TestToolParameterValidator:
    """Test ToolParameterValidator class"""

    def test_validator_creation(self):
        """Test creating a validator"""
        validator = ToolParameterValidator()
        assert validator is not None
        assert isinstance(validator.schemas, dict)

    def test_register_schema(self):
        """Test registering a custom schema"""
        validator = ToolParameterValidator()

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0, "maximum": 150}
            },
            "required": ["name"]
        }

        validator.register_schema("test_tool", schema)
        assert "test_tool" in validator.schemas
        assert validator.schemas["test_tool"] == schema

    def test_validate_required_fields(self):
        """Test validation of required fields"""
        validator = ToolParameterValidator()

        schema = {
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "integer"}
            },
            "required": ["field1", "field2"]
        }

        validator.register_schema("test", schema)

        # Missing required fields
        is_valid, errors = validator.validate("test", {"field1": "value"})
        assert not is_valid
        assert any("field2" in error for error in errors)

        # All required fields present
        is_valid, errors = validator.validate("test", {"field1": "value", "field2": 42})
        assert is_valid
        assert len(errors) == 0

    def test_validate_field_types(self):
        """Test validation of field types"""
        validator = ToolParameterValidator()

        schema = {
            "type": "object",
            "properties": {
                "string_field": {"type": "string"},
                "int_field": {"type": "integer"},
                "bool_field": {"type": "boolean"},
                "array_field": {"type": "array"}
            }
        }

        validator.register_schema("test", schema)

        # Correct types
        is_valid, errors = validator.validate("test", {
            "string_field": "text",
            "int_field": 42,
            "bool_field": True,
            "array_field": [1, 2, 3]
        })
        assert is_valid

        # Wrong types
        is_valid, errors = validator.validate("test", {
            "string_field": 123,  # Should be string
            "int_field": "text"   # Should be integer
        })
        assert not is_valid
        assert len(errors) > 0

    def test_validate_numeric_ranges(self):
        """Test validation of numeric ranges"""
        validator = ToolParameterValidator()

        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "score": {"type": "number", "minimum": 0.0, "maximum": 100.0}
            }
        }

        validator.register_schema("test", schema)

        # Within range
        is_valid, errors = validator.validate("test", {"age": 25, "score": 85.5})
        assert is_valid

        # Out of range
        is_valid, errors = validator.validate("test", {"age": 200})
        assert not is_valid
        assert any("<=" in error or "maximum" in error.lower() for error in errors)

        is_valid, errors = validator.validate("test", {"age": -5})
        assert not is_valid
        assert any(">=" in error or "minimum" in error.lower() for error in errors)

    def test_validate_string_patterns(self):
        """Test validation of string patterns"""
        validator = ToolParameterValidator()

        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string", "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}
            }
        }

        validator.register_schema("test", schema)

        # Valid pattern
        is_valid, errors = validator.validate("test", {"email": "user@example.com"})
        assert is_valid

        # Invalid pattern
        is_valid, errors = validator.validate("test", {"email": "not-an-email"})
        assert not is_valid
        assert any("pattern" in error.lower() for error in errors)

    def test_validate_enum_values(self):
        """Test validation of enum values"""
        validator = ToolParameterValidator()

        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pending", "active", "completed"]}
            }
        }

        validator.register_schema("test", schema)

        # Valid enum value
        is_valid, errors = validator.validate("test", {"status": "active"})
        assert is_valid

        # Invalid enum value
        is_valid, errors = validator.validate("test", {"status": "invalid"})
        assert not is_valid
        assert any("one of" in error.lower() or "enum" in error.lower() for error in errors)

    def test_unknown_tool_returns_valid(self):
        """Test that unknown tools pass validation"""
        validator = ToolParameterValidator()

        # Unknown tool should pass (no schema registered)
        is_valid, errors = validator.validate("unknown_tool", {"any": "params"})
        assert is_valid
        assert len(errors) == 0


class TestStandardSchemas:
    """Test standard tool schemas"""

    def test_register_standard_schemas(self):
        """Test registering standard schemas"""
        from pycode.tool_validation import get_validator
        register_standard_schemas()

        validator = get_validator()

        # Check that standard tools are registered
        standard_tools = ["write", "read", "edit", "bash", "grep", "glob"]
        for tool in standard_tools:
            assert tool in validator.schemas

    def test_write_tool_schema(self):
        """Test write tool schema validation"""
        register_standard_schemas()

        # Valid write parameters
        is_valid, errors = validate_tool_parameters("write", {
            "file_path": "/path/to/file.txt",
            "content": "file content"
        })
        assert is_valid

        # Missing required field
        is_valid, errors = validate_tool_parameters("write", {
            "file_path": "/path/to/file.txt"
        })
        assert not is_valid

    def test_read_tool_schema(self):
        """Test read tool schema validation"""
        register_standard_schemas()

        # Valid read parameters
        is_valid, errors = validate_tool_parameters("read", {
            "file_path": "/path/to/file.txt"
        })
        assert is_valid

        # With optional parameters
        is_valid, errors = validate_tool_parameters("read", {
            "file_path": "/path/to/file.txt",
            "offset": 0,
            "limit": 100
        })
        assert is_valid

        # Invalid offset (negative)
        is_valid, errors = validate_tool_parameters("read", {
            "file_path": "/path/to/file.txt",
            "offset": -5
        })
        assert not is_valid

    def test_bash_tool_schema(self):
        """Test bash tool schema validation"""
        register_standard_schemas()

        # Valid bash parameters
        is_valid, errors = validate_tool_parameters("bash", {
            "command": "ls -la"
        })
        assert is_valid

        # With timeout
        is_valid, errors = validate_tool_parameters("bash", {
            "command": "sleep 5",
            "timeout": 10
        })
        assert is_valid

        # Missing required command
        is_valid, errors = validate_tool_parameters("bash", {})
        assert not is_valid

    def test_grep_tool_schema(self):
        """Test grep tool schema validation"""
        register_standard_schemas()

        # Valid grep parameters
        is_valid, errors = validate_tool_parameters("grep", {
            "pattern": "search.*pattern",
            "path": "/path/to/search"
        })
        assert is_valid

        # With optional parameters
        is_valid, errors = validate_tool_parameters("grep", {
            "pattern": "search",
            "path": "/path",
            "case_sensitive": False,
            "max_results": 50
        })
        assert is_valid

    def test_glob_tool_schema(self):
        """Test glob tool schema validation"""
        register_standard_schemas()

        # Valid glob parameters
        is_valid, errors = validate_tool_parameters("glob", {
            "pattern": "**/*.py",
            "path": "/project"
        })
        assert is_valid


class TestValidateToolParameters:
    """Test validate_tool_parameters function"""

    def test_validate_tool_parameters_function(self):
        """Test the global validate_tool_parameters function"""
        register_standard_schemas()

        # Should work for registered tools
        is_valid, errors = validate_tool_parameters("write", {
            "file_path": "/test.txt",
            "content": "test"
        })
        assert is_valid

        # Should pass for unknown tools
        is_valid, errors = validate_tool_parameters("unknown", {"any": "params"})
        assert is_valid


class TestToolValidationError:
    """Test ToolValidationError exception"""

    def test_tool_validation_error_creation(self):
        """Test creating ToolValidationError"""
        errors = ["Error 1", "Error 2"]
        exc = ToolValidationError("Validation failed", errors=errors)

        assert "Validation failed" in str(exc)
        assert exc.errors == errors

    def test_tool_validation_error_without_errors(self):
        """Test ToolValidationError without specific errors"""
        exc = ToolValidationError("test_tool", [])
        assert "test_tool" in str(exc)
        assert exc.errors == []
