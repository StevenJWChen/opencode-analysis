"""
Configuration System

Manages PyCode configuration with YAML file support.
Allows customization of agents, tools, models, and runtime settings.
Supports environment variable substitution in config files.
"""

import os
import re
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field, ValidationError
import yaml

from .logging import get_logger, LogLevel


class ModelConfig(BaseModel):
    """Model configuration"""
    provider: str = "anthropic"
    model_id: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 4096


class AgentConfigSettings(BaseModel):
    """Agent-specific configuration"""
    name: str
    model: ModelConfig = Field(default_factory=ModelConfig)
    enabled_tools: list[str] = Field(default_factory=list)
    edit_permission: Literal["allow", "deny", "ask"] = "allow"
    bash_permissions: dict[str, Literal["allow", "deny", "ask"]] = Field(default_factory=dict)
    max_iterations: int = 10


class RuntimeConfig(BaseModel):
    """Runtime configuration"""
    verbose: bool = True
    log_level: str = "normal"  # quiet, normal, verbose, debug
    log_file: str | None = None
    auto_approve_tools: bool = False
    max_iterations: int = 10
    doom_loop_threshold: int = 3
    doom_loop_detection: bool = True
    context_window_tokens: int = 100_000
    max_conversation_messages: int = 20


class ProviderSettings(BaseModel):
    """Provider configuration"""
    api_key: str | None = None
    base_url: str | None = None
    timeout: int = 60


class PyCodeConfig(BaseModel):
    """Main PyCode configuration"""

    # Runtime settings
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

    # Default model
    default_model: ModelConfig = Field(default_factory=ModelConfig)

    # Agent configurations
    agents: dict[str, AgentConfigSettings] = Field(default_factory=dict)

    # Provider settings (API keys, etc.)
    providers: dict[str, ProviderSettings] = Field(default_factory=dict)

    # Storage settings
    storage_path: str = "~/.pycode/storage"

    # Tool settings
    enabled_tools: list[str] = Field(default_factory=lambda: [
        "write", "read", "edit", "bash", "grep", "glob", "ls",
        "multiedit", "git", "webfetch", "snapshot", "patch",
        "ask", "todo", "codesearch"
    ])


class ConfigManager:
    """Manages PyCode configuration"""

    DEFAULT_CONFIG_LOCATIONS = [
        Path.home() / ".pycode" / "config.yaml",
        Path.cwd() / ".pycode.yaml",
        Path.cwd() / "pycode.yaml",
    ]

    def __init__(self, config_path: Path | None = None):
        """Initialize config manager

        Args:
            config_path: Optional path to config file. If None, will search default locations.
        """
        self.config_path = config_path
        self._config: PyCodeConfig | None = None
        self.logger = get_logger()

    def _find_config_file(self) -> Path | None:
        """Find config file in default locations"""
        for path in self.DEFAULT_CONFIG_LOCATIONS:
            if path.exists():
                return path
        return None

    def _substitute_env_vars(self, value: Any) -> Any:
        """Recursively substitute environment variables in config values

        Supports ${VAR_NAME} and ${VAR_NAME:default} syntax.

        Examples:
            api_key: ${ANTHROPIC_API_KEY}
            api_key: ${ANTHROPIC_API_KEY:sk-ant-default}
            base_url: ${API_URL:https://api.anthropic.com}
        """
        if isinstance(value, str):
            # Pattern: ${VAR_NAME} or ${VAR_NAME:default}
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

            def replace_var(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""

                env_value = os.getenv(var_name)
                if env_value is None:
                    if default_value:
                        self.logger.debug(
                            f"Using default value for {var_name}",
                            variable=var_name,
                            default=default_value
                        )
                        return default_value
                    else:
                        self.logger.warning(
                            f"Environment variable not set: {var_name}",
                            variable=var_name
                        )
                        return ""
                return env_value

            return re.sub(pattern, replace_var, value)

        elif isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}

        elif isinstance(value, list):
            return [self._substitute_env_vars(item) for item in value]

        return value

    def load(self) -> PyCodeConfig:
        """Load configuration from file or use defaults"""
        if self._config:
            return self._config

        # Try to load from file
        config_file = self.config_path or self._find_config_file()

        if config_file and config_file.exists():
            try:
                self.logger.debug("Loading config", file=str(config_file))

                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f) or {}

                # Substitute environment variables
                config_data = self._substitute_env_vars(config_data)

                # Validate and create config
                self._config = PyCodeConfig.model_validate(config_data)

                self.logger.info("Configuration loaded", file=str(config_file))
                return self._config

            except ValidationError as e:
                self.logger.error(
                    "Config validation failed",
                    file=str(config_file),
                    errors=len(e.errors())
                )

                # Show detailed validation errors
                for error in e.errors():
                    field = " -> ".join(str(x) for x in error["loc"])
                    self.logger.error(
                        f"  {field}: {error['msg']}",
                        type=error["type"]
                    )

                self.logger.warning("Using default configuration due to validation errors")

            except yaml.YAMLError as e:
                self.logger.error(
                    "Failed to parse YAML config",
                    file=str(config_file),
                    error=str(e)
                )
                self.logger.warning("Using default configuration")

            except Exception as e:
                self.logger.error(
                    "Failed to load config",
                    file=str(config_file),
                    error=str(e)
                )
                self.logger.warning("Using default configuration")

        else:
            self.logger.debug("No config file found, using defaults")

        # Use default configuration
        self._config = self._get_default_config()
        return self._config

    def save(self, config: PyCodeConfig, path: Path | None = None) -> None:
        """Save configuration to file

        Args:
            config: Configuration to save
            path: Optional path to save to. If None, uses current config_path or default.
        """
        save_path = path or self.config_path or self.DEFAULT_CONFIG_LOCATIONS[0]

        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save as YAML
        config_dict = config.model_dump(exclude_none=True)

        with open(save_path, "w") as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)

        self.logger.info("Configuration saved", path=str(save_path))

    def _get_default_config(self) -> PyCodeConfig:
        """Get default configuration"""
        return PyCodeConfig(
            runtime=RuntimeConfig(
                verbose=True,
                auto_approve_tools=False,
                max_iterations=10,
                doom_loop_threshold=3,
                doom_loop_detection=True,
            ),
            default_model=ModelConfig(
                provider="anthropic",
                model_id="claude-3-5-sonnet-20241022",
                temperature=0.7,
                max_tokens=4096,
            ),
            agents={
                "build": AgentConfigSettings(
                    name="build",
                    model=ModelConfig(
                        provider="anthropic",
                        model_id="claude-3-5-sonnet-20241022",
                    ),
                    enabled_tools=[
                        "write", "read", "edit", "bash", "grep", "glob",
                        "multiedit", "git", "webfetch", "snapshot", "patch"
                    ],
                    edit_permission="allow",
                    bash_permissions={"*": "allow"},
                    max_iterations=10,
                ),
                "plan": AgentConfigSettings(
                    name="plan",
                    model=ModelConfig(
                        provider="anthropic",
                        model_id="claude-3-5-sonnet-20241022",
                    ),
                    enabled_tools=["read", "grep", "glob", "ls", "codesearch"],
                    edit_permission="deny",
                    bash_permissions={"*": "deny"},
                    max_iterations=5,
                ),
            },
            providers={
                "anthropic": ProviderSettings(
                    api_key=None,  # Load from env
                    base_url=None,
                    timeout=60,
                ),
                "openai": ProviderSettings(
                    api_key=None,  # Load from env
                    base_url=None,
                    timeout=60,
                ),
            },
            storage_path="~/.pycode/storage",
        )

    def create_default_config(self, path: Path | None = None) -> None:
        """Create a default configuration file

        Args:
            path: Optional path to create config at. If None, uses default location.
        """
        default_config = self._get_default_config()
        save_path = path or self.DEFAULT_CONFIG_LOCATIONS[0]
        self.save(default_config, save_path)
        self.logger.info("Default configuration created", path=str(save_path))
        self.logger.info("Customizable settings: runtime.max_iterations, auto_approve_tools, doom_loop_threshold, default_model, agents, providers")
        self.logger.info("Edit the configuration file and restart PyCode to apply changes")

    def get_agent_config(self, agent_name: str) -> AgentConfigSettings | None:
        """Get configuration for a specific agent

        Args:
            agent_name: Name of the agent

        Returns:
            Agent configuration or None if not found
        """
        config = self.load()
        return config.agents.get(agent_name)

    def get_provider_settings(self, provider_name: str) -> ProviderSettings | None:
        """Get settings for a specific provider

        Args:
            provider_name: Name of the provider (e.g., "anthropic", "openai")

        Returns:
            Provider settings or None if not found
        """
        config = self.load()
        return config.providers.get(provider_name)


# Global config manager instance
_config_manager: ConfigManager | None = None


def get_config_manager(config_path: Path | None = None) -> ConfigManager:
    """Get global config manager instance

    Args:
        config_path: Optional path to config file

    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager


def load_config(config_path: Path | None = None) -> PyCodeConfig:
    """Load PyCode configuration

    Args:
        config_path: Optional path to config file

    Returns:
        PyCodeConfig instance
    """
    manager = get_config_manager(config_path)
    return manager.load()
