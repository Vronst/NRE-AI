"""Tests for the BotManager."""

from unittest.mock import MagicMock, call

import pytest
from nre_ai.agent import AIAgent
from nre_ai.bot_state_processor import BotStateProcessor
from nre_ai.manager import BotManager


@pytest.fixture
def mock_processor():
    """Fixture for a mocked BotStateProcessor."""
    return MagicMock(spec=BotStateProcessor)


@pytest.fixture
def mock_agent_factory():
    """Factory for creating mocked AIAgents."""

    def _create_mock_agent(name: str):
        agent = MagicMock(spec=AIAgent)
        agent.name = name
        agent.to_dict.return_value = {"name": name, "zloto": 100}
        return agent

    return _create_mock_agent


def test_manager_initialization(mock_processor):
    """Test that the manager initializes correctly."""
    manager = BotManager(processor=mock_processor)
    assert manager.processor == mock_processor
    assert manager.bots == []


def test_add_bot(mock_processor, mock_agent_factory):
    """Test that bots can be added to the manager."""
    manager = BotManager(processor=mock_processor)
    bot1 = mock_agent_factory("bot1")

    manager.add_bot(bot1)

    assert len(manager.bots) == 1
    assert manager.bots[0] == bot1


def test_run_all_turns_single_bot(mock_processor, mock_agent_factory):
    """Test running a turn for a single registered bot."""
    manager = BotManager(processor=mock_processor)
    bot1 = mock_agent_factory("bot1")
    manager.add_bot(bot1)

    cities_data = {"Miasto": MagicMock()}

    manager.run_all_turns(cities_data)

    # Verify agent's turn was taken
    bot1.take_turn.assert_called_once_with(cities_data)

    # Verify agent's state was converted
    bot1.to_dict.assert_called_once()

    # Verify state was saved
    mock_processor.save_bot_state.assert_called_once_with(bot1.to_dict())


def test_run_all_turns_multiple_bots(mock_processor, mock_agent_factory):
    """Test running turns for multiple registered bots."""
    manager = BotManager(processor=mock_processor)
    bot1 = mock_agent_factory("bot1")
    bot2 = mock_agent_factory("bot2")
    manager.add_bot(bot1)
    manager.add_bot(bot2)

    cities_data = {"Miasto": MagicMock()}

    manager.run_all_turns(cities_data)

    # Check bot1
    bot1.take_turn.assert_called_once_with(cities_data)
    bot1.to_dict.assert_called_once()

    # Check bot2
    bot2.take_turn.assert_called_once_with(cities_data)
    bot2.to_dict.assert_called_once()

    # Check that save was called for both
    assert mock_processor.save_bot_state.call_count == 2
    mock_processor.save_bot_state.assert_has_calls(
        [call(bot1.to_dict()), call(bot2.to_dict())], any_order=True
    )


def test_run_all_turns_no_bots(mock_processor):
    """Test that nothing happens if no bots are registered."""
    manager = BotManager(processor=mock_processor)
    manager.run_all_turns({})

    mock_processor.save_bot_state.assert_not_called()
