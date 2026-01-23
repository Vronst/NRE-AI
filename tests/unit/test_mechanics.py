"""Unit tests for shared mechanics."""

import numpy as np
import pytest

from nre_ai.mechanics import (
    MAX_FEE,
    MAX_INVENTORY_QTY,
    MAX_MONEY,
    MAX_PRICE,
    calculate_net_worth,
    execute_action,
    get_observation,
    sanitize_city_data,
)


# Mock classes for testing
class MockAgent:
    def __init__(self, name="TestBot", money=1000, initial_city="CityA"):
        self.name = name
        self.money = money
        self.current_city_name = initial_city
        self.inventory = {}


class MockCity:
    def __init__(self, name, fee, commodities, connections):
        self.name = name
        self.fee = fee
        self.commodities = commodities
        self.connections = connections


@pytest.fixture
def agent():
    return MockAgent()


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
                "food": {
                    "quantity": 50,
                    "price": 10,
                    "regular_price": 10,
                    "regular_quantity": 100,
                },
            },
            connections=["CityB"],
        ),
        "CityB": MockCity(
            name="CityB",
            fee=20,
            commodities={
                "gems": {
                    "quantity": 5,
                    "price": 150,
                    "regular_price": 100,
                    "regular_quantity": 100,
                },
            },
            connections=["CityA"],
        ),
    }


def test_get_observation_shape(agent, cities):
    obs = get_observation(agent, cities)
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (37,)
    assert obs.dtype == np.float32


def test_get_observation_values(agent, cities):
    # Test specific values in observation
    # Agent money: 1000 / MAX_MONEY
    # Inventory: 0
    # Current City Fee: 10 / MAX_FEE

    obs = get_observation(agent, cities)

    # Money (index 0)
    assert obs[0] == 1000 / MAX_MONEY

    # Inventory (indices 1-5) - all 0
    assert np.all(obs[1:6] == 0)

    # Current City Fee (index 6)
    assert obs[6] == 10 / MAX_FEE


def test_execute_action_buy(agent, cities):
    # Action 0-4 are Buy. Let's buy gems (index 1 in COMMODITIES list: metal, gems, food...)
    # COMMODITIES = ["metal", "gems", "food", "fuel", "relics"]
    # gems is index 1.

    action = 1  # Buy gems

    execute_action(action, agent, cities, verbose=False)

    # Should buy 10 gems (max per turn) at 100 each = 1000 cost
    # Agent had 1000, so money becomes 0
    assert agent.money == 0
    assert "gems" in agent.inventory
    assert agent.inventory["gems"]["quantity"] == 10
    assert cities["CityA"].commodities["gems"]["quantity"] == 0  # 10 - 10


def test_execute_action_sell(agent, cities):
    # Setup inventory
    agent.inventory = {"gems": {"quantity": 10, "avg_buy_price": 100}}
    agent.money = 0

    # Action 5-9 are Sell. gems is index 1 -> action 5+1 = 6
    action = 6

    execute_action(action, agent, cities, verbose=False)

    # Should sell 10 gems at 100 each = 1000 revenue
    assert agent.money == 1000
    assert "gems" not in agent.inventory  # Sold all
    assert cities["CityA"].commodities["gems"]["quantity"] == 20  # 10 + 10


def test_execute_action_travel(agent, cities):
    # Action 11-20 are Travel. Neighbor 0 -> action 11
    action = 11

    did_travel = execute_action(action, agent, cities, verbose=False)

    assert did_travel is True
    assert agent.current_city_name == "CityB"
    assert agent.money == 980  # 1000 - 20 fee


def test_calculate_net_worth(agent, cities):
    agent.money = 500
    agent.inventory = {"gems": {"quantity": 10, "avg_buy_price": 50}}
    # CityA price for gems is 100

    net_worth = calculate_net_worth(agent, cities)

    # 500 + (10 * 100) = 1500
    assert net_worth == 1500


def test_sanitize_city_data():
    # Create data with overflows
    bad_data = [
        {
            "name": "OverflowCity",
            "commodities": {
                "gems": {
                    "price": MAX_PRICE + 1000,
                    "quantity": MAX_INVENTORY_QTY + 500,
                    "regular_price": MAX_PRICE * 2,
                    "regular_quantity": MAX_INVENTORY_QTY * 2,
                }
            },
        }
    ]

    sanitize_city_data(bad_data)

    details = bad_data[0]["commodities"]["gems"]
    assert details["price"] == int(MAX_PRICE)
    assert details["quantity"] == int(MAX_INVENTORY_QTY)
    assert details["regular_price"] == int(MAX_PRICE)
    assert details["regular_quantity"] == int(MAX_INVENTORY_QTY)
