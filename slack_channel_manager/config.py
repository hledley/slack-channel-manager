import json
import re
from enum import Enum
from pathlib import Path
from typing import Callable

import click


class ConfigKey(Enum):
    SUBDOMAIN = "slack_subdomain"
    SECTION_NAME = "slack_channel_section_name"
    SECTION_EMOJI = "slack_channel_section_emoji"
    CHANNEL_REGEX = "slack_channel_regex"
    D_COOKIE = "slack_d_cookie"


class ConfigManager:
    def __init__(self, filename: str = "secret_config.json") -> None:
        self.file_path: Path = Path(filename)
        self.data: dict[str, any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load data from the JSON config file."""
        if self.file_path.exists():
            with self.file_path.open("r") as file:
                try:
                    self.data = json.load(file)
                except json.JSONDecodeError:
                    raise ValueError(
                        f"The config file {self.file_path} contains invalid JSON."
                    )

    def _save_config(self) -> None:
        """Save data to the JSON config file."""
        with self.file_path.open("w") as file:
            json.dump(self.data, file, indent=4)

    def is_configured(self) -> bool:
        """Check if the config file has all the required keys."""
        return all(key.value in self.data for key in ConfigKey)

    def get(self, key: ConfigKey, default: any = None, required: bool = True) -> any:
        """Retrieve a value from the config. Differs from standard gets in that it errors on missing values by default."""
        value = self.data.get(key.value, default)
        if required and not value:
            raise ValueError(f"Missing required configuration key: {key}")

        return value

    def upsert(self, key: ConfigKey, value: any) -> None:
        """Update or insert a value in the config and save."""
        if key in ConfigKey:
            self.data[key.value] = value
            self._save_config()
        else:
            raise ValueError(f"Invalid configuration key: {key}")

    def delete(self, key: ConfigKey) -> None:
        """Delete a key from the config and save."""
        if key.value in self.data:
            del self.data[key.value]
            self._save_config()

    def __dict__(self) -> dict[str, any]:
        return self.data


def reload_config(
    config: ConfigManager, d_cookie_fetcher: Callable[[str], str]
) -> None:
    subdomain = (
        click.prompt(
            "Slack subdomain (e.g., 'foo' in 'foo.slack.com')",
            type=str,
            default=config.get(ConfigKey.SUBDOMAIN, required=False),
            show_default=True
            if config.get(ConfigKey.SUBDOMAIN, required=False)
            else False,
        )
        .strip()
        .lower()
    )
    if "." in subdomain or "/" in subdomain:
        raise ValueError("Invalid subdomain")
    config.upsert(ConfigKey.SUBDOMAIN, subdomain)

    section_name = (
        click.prompt(
            "Name of section for grouped channels (e.g., 'incidents')",
            type=str,
            default=config.get(ConfigKey.SECTION_NAME, "incidents"),
            show_default=True,
        )
        .strip()
        .lower()
    )
    if " " in section_name:
        raise ValueError("Invalid section name")
    config.upsert(ConfigKey.SECTION_NAME, section_name)

    section_emoji = (
        click.prompt(
            "Emoji for section for grouped channels (e.g., 'fire' for :fire:)",
            type=str,
            default=config.get(ConfigKey.SECTION_EMOJI, "fire"),
            show_default=True,
        )
        .strip()
        .lower()
    )
    if " " in section_emoji:
        raise ValueError("Invalid section emoji")
    config.upsert(ConfigKey.SECTION_EMOJI, section_emoji)

    channel_regex = click.prompt(
        "Regex for channels to sort (e.g., '^inc-', can be partial match)",
        type=str,
        default=config.get(ConfigKey.CHANNEL_REGEX, "^inc-"),
        show_default=True,
    )
    try:
        re.compile(channel_regex)
    except re.error:
        raise ValueError("Invalid regex")
    config.upsert(ConfigKey.CHANNEL_REGEX, channel_regex)

    if not config.get(ConfigKey.D_COOKIE, required=False) or click.confirm(
        "Re-authenticate to Slack?"
    ):
        click.echo(
            "Next we'll open a browser window. Log in to slack, and this script will capture your session cookie."
        )
        click.confirm("Enter y to continue...", abort=True)
        config.upsert(
            ConfigKey.D_COOKIE, d_cookie_fetcher(config.get(ConfigKey.SUBDOMAIN))
        )

    click.echo("Configuration saved!\n")
