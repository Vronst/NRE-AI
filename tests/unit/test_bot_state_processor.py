"""Tests for the BotStateProcessor."""

import os
import shutil

import pytest

from nre_ai.bot_state_processor import BotStateProcessor


@pytest.fixture
def test_dir():
    """Fixture to create and clean up a temporary directory for tests."""
    directory = "test_bot_states"
    yield directory
    if os.path.exists(directory):
        shutil.rmtree(directory)


@pytest.fixture
def bot_data():
    """Fixture providing sample bot data."""
    return {
        "name": "test_bot_1",
        "zloto": 1000,
        "ekwipunek": {"metal": 10, "gems": 5, "food": 20, "fuel": 15, "relics": 1},
    }


def test_initialization_with_direct_path(test_dir):
    """Test initialization with a directly provided path."""
    processor = BotStateProcessor(test_dir)
    assert processor.base_path == test_dir
    assert os.path.exists(test_dir)


def test_initialization_with_env_variable(monkeypatch):
    """Test initialization using an environment variable."""
    env_path = "env_test_path"
    monkeypatch.setenv("BOT_STATE_PATH", env_path)

    try:
        processor = BotStateProcessor()
        assert processor.base_path == env_path
        assert os.path.exists(env_path)
    finally:
        if os.path.exists(env_path):
            shutil.rmtree(env_path)


def test_initialization_fails_if_no_path_provided(monkeypatch):
    """Test that initialization fails if no path is given."""
    monkeypatch.delenv("BOT_STATE_PATH", raising=False)

    with pytest.raises(ValueError):
        BotStateProcessor()


def test_save_and_load_bot_state(test_dir, bot_data):
    """Test saving and loading a bot's state."""
    processor = BotStateProcessor(test_dir)
    processor.save_bot_state(bot_data)

    expected_path = os.path.join(test_dir, "test_bot_1.json")
    assert os.path.exists(expected_path)

    loaded_data = processor.load_bot_state("test_bot_1")
    assert loaded_data == bot_data


def test_load_nonexistent_bot(test_dir):
    """Test loading a bot that doesn't exist."""
    processor = BotStateProcessor(test_dir)
    loaded_data = processor.load_bot_state("nonexistent_bot")
    assert loaded_data is None


def test_save_bot_state_no_name(test_dir, bot_data):
    """Test saving a bot state without a name."""
    processor = BotStateProcessor(test_dir)
    bot_data_no_name = bot_data.copy()
    del bot_data_no_name["name"]

    with pytest.raises(KeyError):
        processor.save_bot_state(bot_data_no_name)


def test_multiple_bots(test_dir, bot_data):
    """Test saving and loading multiple bots."""
    processor = BotStateProcessor(test_dir)
    bot_2_data = {
        "name": "test_bot_2",
        "zloto": 500,
        "ekwipunek": {"metal": 5, "gems": 2},
    }

    processor.save_bot_state(bot_data)
    processor.save_bot_state(bot_2_data)

    loaded_1 = processor.load_bot_state("test_bot_1")
    loaded_2 = processor.load_bot_state("test_bot_2")

    assert loaded_1 == bot_data
    assert loaded_2 == bot_2_data
