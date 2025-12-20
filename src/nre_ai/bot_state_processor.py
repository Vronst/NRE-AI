"""Handles the persistence of game bots."""

import json
import os


class BotStateProcessor:
    """Manages saving and loading of bot states."""

    def __init__(self, base_path: str | None = None):
        """Initializes the BotStateProcessor.

        Args:
            base_path (str | None): The directory where bot state files are
                stored. If None, it defaults to the value of the
                'BOT_STATE_PATH' environment variable.

        Raises:
            ValueError: If base_path is not provided and 'BOT_STATE_PATH'
                is not set.
        """
        if base_path is None:
            base_path = os.getenv("BOT_STATE_PATH")
            if not base_path:
                raise ValueError(
                    "base_path must be provided or 'BOT_STATE_PATH'"
                    + " environment variable must be set."
                )

        self.base_path: str = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _get_bot_file_path(self, bot_name: str) -> str:
        """Constructs the file path for a given bot name.

        Args:
            bot_name (str): The unique name of the bot.

        Returns:
            str: The full path to the bot's JSON file.
        """
        return os.path.join(self.base_path, f"{bot_name}.json")

    def save_bot_state(self, bot_data: dict):
        """Saves the bot's current state to a JSON file.

        Args:
            bot_data (dict): The bot's state data, including a 'name' key.

        Raises:
            KeyError: If 'name' is not in bot_data.
        """
        if "name" not in bot_data:
            raise KeyError("Bot data must include a 'name' for identification.")

        bot_name = bot_data["name"]
        file_path = self._get_bot_file_path(bot_name)

        with open(file_path, "w") as f:
            json.dump(bot_data, f, indent=2)
        print(f"Bot state for '{bot_name}' saved to {file_path}")

    def load_bot_state(self, bot_name: str) -> dict | None:
        """Loads the bot's state from a file.

        Args:
            bot_name (str): The unique name of the bot.

        Returns:
            dict | None: The loaded bot data, or None if the
                file doesn't exist.
        """
        file_path = self._get_bot_file_path(bot_name)
        if not os.path.exists(file_path):
            return None

        with open(file_path) as f:
            return json.load(f)
