"""This module contains class for loading and saving data to json."""

import json


class JsonManager:
    """Loads and saves data from to json file."""

    def __init__(self, path: str) -> None:
        """Initialize DataLoader.

        Args:
            path (str): path to json file (for saving and loading).

        Returns:
            None
        """
        self(path)

    def __call__(self, path: str | None = None) -> None:
        """Load data with DataLoader.

        Uses path from initialization if not provided.

        Args:
            path (str | None): path to json file (for saving and loading),
                default None.

        Returns:
            None
        """
        self.path = path if path else self.path
        self.__load()

    def __load(self) -> dict:
        with open(self.path) as file:
            self.data = json.load(file)
        return self.data

    @property
    def cities_after(self) -> list[dict]:
        """Returns list of cities after changes.

        Returns:
            list: list of cities.
        """
        return self.data["after"]

    @property
    def cities_before(self) -> list:
        """Returns list of cities after changes.

        Returns:
            list[dict]: list of cities before changes.
        """
        return self.data["cities"]

    def save(self, data: dict) -> None:
        """Saves data to json file.
        
        Args:
            data (dict): dict with cities data.

        Returns:
            None
        """
        with open(self.path, 'w') as file:
            json.dump(data, file, indent=2)
