"""Unit tests for TradingEnv."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from nre_ai.trading_env import TradingEnv


@pytest.fixture
def mock_dependencies():
    with (
        patch("nre_ai.trading_env.JsonManager") as mock_json,
        patch("nre_ai.trading_env.CityProcessor") as mock_proc,
    ):
        # Setup mock processor behavior
        mock_proc_instance = mock_proc.return_value

        # Mock initial cities
        mock_city = MagicMock()
        mock_city.name = "CityA"
        mock_city.fee = 10
        mock_city.commodities = {}
        mock_city.connections = []

        mock_proc_instance.get_dict_of_cities.return_value = {"CityA": mock_city}

        yield mock_json, mock_proc_instance


def test_initialization(mock_dependencies):
    env = TradingEnv("dummy_path.json")

    assert env.action_space.n == 21  # 5 buy + 5 sell + 1 sell_all + 10 travel
    assert env.observation_space.shape == (37,)
    assert env.current_step == 0


def test_reset(mock_dependencies):
    env = TradingEnv("dummy_path.json")
    # __init__ calls reset, so we check if it was called
    assert env.city_processor.process_changes.call_count == 1

    obs, info = env.reset()

    assert isinstance(obs, np.ndarray)
    assert obs.shape == (37,)
    assert info == {}
    assert env.current_step == 0
    assert env.agent.name == "TrainingBot"
    # Called again
    assert env.city_processor.process_changes.call_count == 2


def test_step_structure(mock_dependencies):
    env = TradingEnv("dummy_path.json")
    # Reset mock count to ignore init calls
    env.city_processor.process_changes.reset_mock()

    # Action 0 (Buy metal)
    action = 0

    with (
        patch("nre_ai.trading_env.execute_action") as mock_exec,
        patch("nre_ai.trading_env.calculate_net_worth") as mock_calc,
    ):
        mock_exec.return_value = False  # Did not travel
        mock_calc.return_value = 1000.0  # Net worth

        obs, reward, terminated, truncated, info = env.step(action)

        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

        mock_exec.assert_called_once()


def test_economy_update_trigger(mock_dependencies):
    env = TradingEnv("dummy_path.json")
    # Reset mock count to ignore init calls
    env.city_processor.process_changes.reset_mock()

    # Mock execute_action to NOT travel
    with patch("nre_ai.trading_env.execute_action", return_value=False):
        # Step 1-3: No update
        for _ in range(3):
            env.step(0)
            env.city_processor.process_changes.assert_not_called()

        # Step 4: Should trigger update (max_local_actions = 4)
        env.step(0)
        env.city_processor.process_changes.assert_called_once()


def test_travel_triggers_update(mock_dependencies):
    env = TradingEnv("dummy_path.json")
    # Reset mock count to ignore init calls
    env.city_processor.process_changes.reset_mock()

    # Mock execute_action to return True (Traveled)
    with patch("nre_ai.trading_env.execute_action", return_value=True):
        env.step(11)  # Travel action

        # Should trigger update immediately
        env.city_processor.process_changes.assert_called_once()


def test_bankruptcy_termination(mock_dependencies):
    env = TradingEnv("dummy_path.json")

    env.agent.money = 0
    env.agent.inventory = {}

    with patch("nre_ai.trading_env.execute_action", return_value=False):
        _, reward, terminated, _, _ = env.step(0)

        assert terminated is True
        assert reward <= -10.0  # Penalty applied


def test_max_steps_truncation(mock_dependencies):
    env = TradingEnv("dummy_path.json")
    env.max_steps = 5

    with patch("nre_ai.trading_env.execute_action", return_value=False):
        for _ in range(4):
            _, _, _, truncated, _ = env.step(0)
            assert truncated is False

        _, _, _, truncated, _ = env.step(0)
        assert truncated is True
