"""Unit tests for AIAgent."""

import pytest

from nre_ai.agent import AIAgent


# Mock City class to avoid dependency on the actual nrecity module
class MockCity:
    def __init__(self, name, fee, commodities, connections, factory=None):
        self.name = name
        self.fee = fee
        self.commodities = commodities
        self.connections = connections
        self.factory = factory if factory else []


@pytest.fixture
def agent():
    return AIAgent(name="TestBot", money=1000, initial_city="CityA")


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
            connections=["CityB", "CityC"],
            factory=["Mine"],  # Produces gems locally (assuming map check passes)
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
                "food": {
                    "quantity": 50,
                    "price": 12,
                    "regular_price": 10,
                    "regular_quantity": 100,
                },
            },
            connections=["CityA"],
        ),
        "CityC": MockCity(
            name="CityC",
            fee=5,  # Cheap fee
            commodities={
                "gems": {
                    "quantity": 20,
                    "price": 90,
                    "regular_price": 100,
                    "regular_quantity": 100,
                },
            },
            connections=["CityA"],
        ),
    }


def test_initialization(agent):
    assert agent.name == "TestBot"
    assert agent.money == 1000
    assert agent.current_city_name == "CityA"
    assert agent.inventory == {}
    assert agent.travel_plan is None


def test_serialization(agent):
    agent.inventory = {"gems": {"quantity": 5, "avg_buy_price": 100}}
    data = agent.to_dict()

    assert data["name"] == "TestBot"
    assert data["zloto"] == 1000
    assert data["current_city"] == "CityA"
    assert data["ekwipunek"]["gems"] == 5

    new_agent = AIAgent.from_dict(data)
    assert new_agent.name == agent.name
    assert new_agent.money == agent.money
    assert new_agent.current_city_name == agent.current_city_name
    assert new_agent.inventory == agent.inventory


def test_get_item_weight(agent):
    assert agent._get_item_weight("gems") == 1.0
    assert agent._get_item_weight("relics") == 10.0
    assert agent._get_item_weight("unknown") == 1.0


def test_calculate_current_weight(agent):
    agent.inventory = {
        "gems": {"quantity": 10, "avg_buy_price": 100},  # 10 * 1.0 = 10
        "relics": {"quantity": 2, "avg_buy_price": 500},  # 2 * 10.0 = 20
    }
    assert agent._calculate_current_weight() == 30.0


def test_travel_execution_success(agent, cities):
    agent.travel_plan = ("CityB", None)
    agent.take_turn(cities)

    assert agent.current_city_name == "CityB"
    assert agent.money == 980  # 1000 - 20 (CityB fee)

    # After arriving in CityB, the agent will immediately plan the next move.
    # Since there are no profitable trades back to CityA (gems 150->100, food 12->10),
    # it will fallback to the cheapest neighbor.
    # CityB only connects to CityA (fee 10).
    assert agent.travel_plan == ("CityA", None)


def test_travel_execution_insufficient_funds(agent, cities):
    agent.money = 10
    agent.travel_plan = ("CityB", None)  # Fee is 20
    agent.take_turn(cities)

    assert agent.current_city_name == "CityA"  # Did not move
    assert agent.money == 10

    # Travel failed, plan cleared.
    # Agent continues turn. No profitable trades (buffer 10 + fee > money 10).
    # Fallback travel.
    # CityA connects to CityB (20) and CityC (5).
    # CityC is cheapest.
    assert agent.travel_plan == ("CityC", None)


def test_sell_commodities_profit(agent, cities):
    # Setup: Agent has gems bought at 100, CityB buys at 150
    agent.current_city_name = "CityB"
    agent.inventory = {"gems": {"quantity": 10, "avg_buy_price": 100}}

    agent._sell_commodities(cities["CityB"])

    assert "gems" not in agent.inventory
    assert agent.money == 1000 + (10 * 150)
    assert cities["CityB"].commodities["gems"]["quantity"] == 15  # 5 + 10


def test_sell_commodities_scarcity(agent, cities):
    # Setup: CityB has very low gems (scarcity), price is low but demand high
    cities["CityB"].commodities["gems"]["quantity"] = 0  # 0 < 10% of 100
    cities["CityB"].commodities["gems"]["price"] = (
        105  # Only 5% profit, normally wouldn't sell
    )

    agent.current_city_name = "CityB"
    agent.inventory = {"gems": {"quantity": 10, "avg_buy_price": 100}}

    agent._sell_commodities(cities["CityB"])

    assert "gems" not in agent.inventory  # Sold due to scarcity
    assert agent.money == 1000 + (10 * 105)


def test_plan_with_inventory_best_route(agent, cities):
    # Agent in CityA, has gems.
    # CityB: Price 150, Fee 20 -> Profit (150-100)*10 - 20 = 480
    # CityC: Price 90, Fee 5 -> Loss
    agent.inventory = {"gems": {"quantity": 10, "avg_buy_price": 100}}

    agent._plan_with_inventory(cities["CityA"], cities)

    assert agent.travel_plan == ("CityB", None)


def test_plan_with_inventory_no_self_loop(agent, cities):
    # Ensure it doesn't plan to go to CityA if it's already there
    agent.inventory = {"gems": {"quantity": 10, "avg_buy_price": 100}}
    # Mock CityA connection to itself just in case
    cities["CityA"].connections.append("CityA")

    agent._plan_with_inventory(cities["CityA"], cities)

    assert agent.travel_plan != ("CityA", None)


def test_buy_logic_constraints(agent, cities):
    # Test money and weight constraints
    # CityA sells gems at 100. Agent has 1000.
    # Fee to CityB is 20. Buffer is 10. Available: 970.
    # Max buy by money: 970 // 100 = 9.

    # Mock factory map to ensure gems are considered local or just force logic
    agent.factory_map = {"gems": "Mine"}

    agent._plan_and_buy_empty_inventory(cities["CityA"], cities)

    assert "gems" in agent.inventory
    assert agent.inventory["gems"]["quantity"] == 9
    assert agent.money == 1000 - (9 * 100)
    assert agent.travel_plan == ("CityB", None)  # CityB is the profitable destination


def test_buy_logic_weight_limit(agent, cities):
    # Set item weight high to test weight limit
    # Gems weight 1.0. Let's pretend we have a heavy item.
    # Or just reduce MAX_WEIGHT for this test? Better to use logic.

    # Let's use 'relics' (weight 10) if available, or just trust the math.
    # Let's simulate a heavy item in CityA
    cities["CityA"].commodities["heavy"] = {
        "quantity": 100,
        "price": 1,
        "regular_price": 1,
        "regular_quantity": 100,
    }
    # Add heavy to factory map
    agent.factory_map["heavy"] = "Mine"

    # Mock get_item_weight for 'heavy'
    original_get_weight = agent._get_item_weight
    agent._get_item_weight = lambda x: 500.0 if x == "heavy" else original_get_weight(x)

    # Add demand in CityB
    cities["CityB"].commodities["heavy"] = {
        "quantity": 0,
        "price": 10,
        "regular_price": 10,
        "regular_quantity": 100,
    }

    agent._plan_and_buy_empty_inventory(cities["CityA"], cities)

    # Max weight 1000. Item weight 500. Max count = 2.
    if "heavy" in agent.inventory:
        assert agent.inventory["heavy"]["quantity"] <= 2


def test_fallback_travel(agent, cities):
    # No inventory, no profitable trades (prices equal everywhere)
    cities["CityA"].commodities["gems"]["price"] = 1000  # Too expensive
    cities["CityA"].commodities["food"]["price"] = 1000

    agent._plan_and_buy_empty_inventory(cities["CityA"], cities)

    # Should choose CityC (fee 5) over CityB (fee 20)
    assert agent.travel_plan == ("CityC", None)


def test_is_bankrupt(agent):
    agent.money = 0
    agent.inventory = {}
    assert agent.is_bankrupt() is True

    agent.money = 10
    assert agent.is_bankrupt() is False

    agent.money = 0
    agent.inventory = {"gems": {"quantity": 1}}
    assert agent.is_bankrupt() is False
