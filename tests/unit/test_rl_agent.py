"""Unit tests for RLAgent."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from nre_ai.rl_agent import RLAgent


# Mock City class
class MockCity:
    def __init__(self, name, fee, commodities, connections):
        self.name = name
        self.fee = fee
        self.commodities = commodities
        self.connections = connections


@pytest.fixture
def cities():
    return {
        "CityA": MockCity(
            name="CityA",
            fee=10,
            commodities={
                "gems": {
                    "quantity": 10,
                    "price": 100,
                    "regular_price": 100,
                    "regular_quantity": 100,
                },
            },
            connections=["CityB"],
        ),
        "CityB": MockCity(name="CityB", fee=20, commodities={}, connections=["CityA"]),
    }


@pytest.fixture
def mock_ppo():
    with patch("nre_ai.rl_agent.PPO") as mock:
        yield mock


def test_initialization(mock_ppo):
    mock_model = MagicMock()
    mock_ppo.load.return_value = mock_model

    agent = RLAgent("Bot1", 1000, "CityA", "dummy_path.zip")

    assert agent.name == "Bot1"
    assert agent.money == 1000
    assert agent.model == mock_model
    mock_ppo.load.assert_called_with("dummy_path.zip")


def test_take_turn(mock_ppo, cities):
    mock_model = MagicMock()
    # Mock predict to return action 0 (Buy metal - index 0)
    mock_model.predict.return_value = (0, None)
    mock_ppo.load.return_value = mock_model

    agent = RLAgent("Bot1", 1000, "CityA", "dummy_path.zip")

    # Patch execute_action to verify it's called correctly
    with patch("nre_ai.rl_agent.execute_action") as mock_execute:
        agent.take_turn(cities)

        # Verify predict was called with an observation
        mock_model.predict.assert_called_once()
        args, _ = mock_model.predict.call_args
        obs = args[0]
        assert isinstance(obs, np.ndarray)

        # Verify execute_action was called with action 0
        mock_execute.assert_called_once_with(0, agent, cities, verbose=True)


def test_serialization(mock_ppo):
    mock_ppo.load.return_value = MagicMock()
    agent = RLAgent("Bot1", 1000, "CityA", "model.zip")
    agent.inventory = {"gems": {"quantity": 5}}

    data = agent.to_dict()
    assert data["name"] == "Bot1"
    assert data["model_path"] == "model.zip"

    # Test from_dict
    new_agent = RLAgent.from_dict(data)
    assert new_agent.name == "Bot1"
    assert new_agent.model_path == "model.zip"
    assert new_agent.inventory == agent.inventory


def test_from_dict_missing_path(mock_ppo):
    data = {
        "name": "Bot1",
        "zloto": 1000,
        "current_city": "CityA",
        # Missing model_path
    }
    with pytest.raises(ValueError):
        RLAgent.from_dict(data)
