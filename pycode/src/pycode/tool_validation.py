"""
Tool Parameter Validation

Validates tool parameters before execution to catch errors early.
Provides detailed error messages for invalid parameters.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, ValidationError, create_model
from .logging import get_logger


class ToolValidationError(Exception):
    """Raised when tool parameters are invalid"""
    def __init__(self, tool_name: str, errors: list[str]):
        self.tool_name = tool_name
        self.errors = errors
        message = f"Invalid parameters for tool '{tool_name}':\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)


class ToolParameterValidator:
    """Validates tool parameters against schemas"""

    def __init__(self):
        self.logger = get_logger()
        self.schemas: Dict[str, Dict[str, Any]] = {}

    def register_schema(self, tool_name: str, schema: Dict[str, Any]):
        """Register a parameter schema for a tool

        Args:
            tool_name: Name of the tool
            schema: JSON schema for parameters
        """
        self.schemas[tool_name] = schema
        self.logger.debug(f"Registered schema for tool", tool=tool_name)

    def validate(self, tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate parameters against registered schema

        Args:
            tool_name: Name of the tool
            parameters: Parameters to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        if tool_name not in self.schemas:
            # No schema registered - allow all parameters
            self.logger.debug(f"No schema registered for tool", tool=tool_name)
            return (True, [])

        schema = self.schemas[tool_name]
        errors = []

        # Validate required fields
        required = schema.get("required", [])
        for field in required:
            if field not in parameters:
                errors.append(f"Missing required parameter: {field}")

        # Validate field types
        properties = schema.get("properties", {})
        for field, value in parameters.items():
            if field not in properties:
                # Extra field - warn but don't fail
                self.logger.warning(f"Unknown parameter for tool", tool=tool_name, parameter=field)
                continue

            field_schema = properties[field]
            field_type = field_schema.get("type")

            # Type validation
            if field_type:
                if not self._validate_type(value, field_type):
                    errors.append(
                        f"Parameter '{field}' should be type '{field_type}', got '{type(value).__name__}'"
                    )

            # Enum validation
            if "enum" in field_schema:
                if value not in field_schema["enum"]:
                    errors.append(
                        f"Parameter '{field}' must be one of {field_schema['enum']}, got '{value}'"
                    )

            # Pattern validation (for strings)
            if field_type == "string" and "pattern" in field_schema:
                import re
                if not re.match(field_schema["pattern"], str(value)):
                    errors.append(
                        f"Parameter '{field}' does not match required pattern: {field_schema['pattern']}"
                    )

            # Range validation (for numbers)
            if field_type in ["integer", "number"]:
                if "minimum" in field_schema and value < field_schema["minimum"]:
                    errors.append(
                        f"Parameter '{field}' must be >= {field_schema['minimum']}, got {value}"
                    )
                if "maximum" in field_schema and value > field_schema["maximum"]:
                    errors.append(
                        f"Parameter '{field}' must be <= {field_schema['maximum']}, got {value}"
                    )

            # Length validation (for strings/arrays)
            if field_type == "string":
                if "minLength" in field_schema and len(str(value)) < field_schema["minLength"]:
                    errors.append(
                        f"Parameter '{field}' must be at least {field_schema['minLength']} characters"
                    )
                if "maxLength" in field_schema and len(str(value)) > field_schema["maxLength"]:
                    errors.append(
                        f"Parameter '{field}' must be at most {field_schema['maxLength']} characters"
                    )

        if errors:
            self.logger.warning(
                f"Parameter validation failed for tool",
                tool=tool_name,
                errors=len(errors)
            )
            return (False, errors)

        self.logger.debug(f"Parameters validated successfully", tool=tool_name)
        return (True, [])

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type

        Args:
            value: Value to check
            expected_type: Expected type name (JSON schema type)

        Returns:
            True if type matches
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        if expected_type not in type_map:
            return True  # Unknown type - allow

        expected = type_map[expected_type]
        return isinstance(value, expected)

    def validate_or_raise(self, tool_name: str, parameters: Dict[str, Any]):
        """Validate parameters and raise exception if invalid

        Args:
            tool_name: Name of the tool
            parameters: Parameters to validate

        Raises:
            ToolValidationError: If parameters are invalid
        """
        is_valid, errors = self.validate(tool_name, parameters)
        if not is_valid:
            raise ToolValidationError(tool_name, errors)


# Global validator instance
_validator: Optional[ToolParameterValidator] = None


def get_validator() -> ToolParameterValidator:
    """Get global validator instance"""
    global _validator
    if _validator is None:
        _validator = ToolParameterValidator()
    return _validator


def register_tool_schema(tool_name: str, schema: Dict[str, Any]):
    """Register a tool schema"""
    get_validator().register_schema(tool_name, schema)


def validate_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate tool parameters"""
    return get_validator().validate(tool_name, parameters)


def validate_tool_parameters_or_raise(tool_name: str, parameters: Dict[str, Any]):
    """Validate tool parameters and raise if invalid"""
    get_validator().validate_or_raise(tool_name, parameters)


# Standard tool schemas
STANDARD_TOOL_SCHEMAS = {
    "write": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["file_path", "content"]
    },
    "read": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read"
            },
            "offset": {
                "type": "integer",
                "minimum": 0,
                "description": "Line number to start reading from"
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "description": "Maximum number of lines to read"
            }
        },
        "required": ["file_path"]
    },
    "edit": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to edit"
            },
            "old_string": {
                "type": "string",
                "description": "String to replace"
            },
            "new_string": {
                "type": "string",
                "description": "Replacement string"
            }
        },
        "required": ["file_path", "old_string", "new_string"]
    },
    "bash": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute"
            },
            "working_directory": {
                "type": "string",
                "description": "Working directory for command"
            },
            "timeout": {
                "type": "integer",
                "minimum": 1,
                "maximum": 600,
                "description": "Timeout in seconds"
            }
        },
        "required": ["command"]
    },
    "grep": {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Search pattern (regex)"
            },
            "path": {
                "type": "string",
                "description": "Path to search in"
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Case-sensitive search"
            }
        },
        "required": ["pattern"]
    },
    "glob": {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match"
            },
            "path": {
                "type": "string",
                "description": "Base path to search in"
            }
        },
        "required": ["pattern"]
    }
}


def register_standard_schemas():
    """Register all standard tool schemas"""
    validator = get_validator()
    for tool_name, schema in STANDARD_TOOL_SCHEMAS.items():
        validator.register_schema(tool_name, schema)
