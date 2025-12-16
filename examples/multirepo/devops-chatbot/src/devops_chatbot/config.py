"""Local configuration for DevOps Assistant.

Extend MACSDKConfig to add your own settings.
"""

from pydantic_settings import SettingsConfigDict

from macsdk.core import MACSDKConfig


class DevopsChatbotConfig(MACSDKConfig):
    """Configuration for DevOps Assistant.

    Add your chatbot-specific settings here.
    They will be loaded from environment variables or .env file.

    Example:
        # In .env:
        MY_CUSTOM_SETTING=value

        # Access in code:
        from .config import config
        print(config.my_custom_setting)
    """

    # Add your custom settings here:
    # my_custom_setting: str | None = None
    # debug_mode: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


config = DevopsChatbotConfig()
