<<<<<<< HEAD
# ruff: noqa
=======
>>>>>>> main
"""Tests for the AIAgent class."""

import random

import pytest
<<<<<<< HEAD
=======
from nrecity import factory as nrecity_factory_map
>>>>>>> main

from nre_ai.agent import AIAgent as Agent

# A default city name for agents that don't need a specific one
DEFAULT_CITY = "test_city"


@pytest.fixture
def agent_factory():
    """Factory to create agents for tests."""
<<<<<<< HEAD

    def _create_agent(name="test_agent", money=1000, city=DEFAULT_CITY, factory_map=None):
        return Agent(name=name, money=money, initial_city=city, factory_map=factory_map)

=======
    def _create_agent(name="test_agent", money=1000, city=DEFAULT_CITY, factory_map=None):
        return Agent(name=name, money=money, initial_city=city, factory_map=factory_map)
>>>>>>> main
    return _create_agent


class TestAgentInitialization:
    """Tests for the agent's constructor and initial state."""

    def test_to_dict_conversion(self, agent_factory):
        """Verify that the to_dict method formats data correctly."""
        agent = agent_factory(name="bot1", money=500)
        agent.inventory = {
            "metal": {"quantity": 20, "avg_buy_price": 10},
            "food": {"quantity": 100, "avg_buy_price": 2},
        }

        expected_dict = {
            "name": "bot1",
            "zloto": 500,
            "ekwipunek": {
                "metal": 20,
                "food": 100,
            },
        }
        assert agent.to_dict() == expected_dict

    def test_to_dict_empty_inventory(self, agent_factory):
        """Verify to_dict works with an empty inventory."""
        agent = agent_factory(name="bot2", money=100)
        expected_dict = {
            "name": "bot2",
            "zloto": 100,
            "ekwipunek": {},
        }
        assert agent.to_dict() == expected_dict


class TestAgentBankruptcy:
    """Tests for the is_bankrupt method."""

    @pytest.mark.parametrize(
        "money, has_inventory, expected",
        [
<<<<<<< HEAD
            (0, False, True),  # Bankrupt: No money, no items
            (-100, False, True),  # Bankrupt: Debt, no items
            (1, False, False),  # Not bankrupt: Has a little money
            (0, True, False),  # Not bankrupt: No money, but has items to sell
=======
            (0, False, True),      # Bankrupt: No money, no items
            (-100, False, True),   # Bankrupt: Debt, no items
            (1, False, False),     # Not bankrupt: Has a little money
            (0, True, False),      # Not bankrupt: No money, but has items to sell
>>>>>>> main
        ],
    )
    def test_bankruptcy_conditions(self, agent_factory, money, has_inventory, expected):
        """Test various bankruptcy scenarios."""
        agent = agent_factory(money=money)
        if has_inventory:
            agent.inventory = {"metal": {"quantity": 1, "avg_buy_price": 1}}
        else:
            agent.inventory = {}
<<<<<<< HEAD

=======
        
>>>>>>> main
        assert agent.is_bankrupt() == expected


class TestAgentProductionCheck:
    """Tests for the _is_produced_locally method."""

    @pytest.mark.regression
    def test_is_produced_locally(self, agent_factory, city_factory):
        """Check local production logic."""
        metal_factory_name = "Huta"
        metal_item_name = "metal"
<<<<<<< HEAD

        # Create a custom factory map for this test
        custom_factory_map = {metal_item_name: metal_factory_name}

=======
        
        # Create a custom factory map for this test
        custom_factory_map = {metal_item_name: metal_factory_name}
        
>>>>>>> main
        agent = agent_factory(factory_map=custom_factory_map)

        city_with_factory = city_factory(factory=[metal_factory_name])
        city_without_factory = city_factory(factory=[])

        assert agent._is_produced_locally(city_with_factory, metal_item_name)
        assert not agent._is_produced_locally(city_without_factory, metal_item_name)


class TestAgentTravelPlanning:
    """Tests for the _plan_next_travel method."""

<<<<<<< HEAD
    def test_plan_next_travel_prefers_selling_inventory(
        self, agent_factory, city_factory
    ):
        """AI should prioritize selling existing inventory for profit."""
        a = city_factory("A", connections=["B"])
        b = city_factory(
            "B", fee=5, commodities={"item1": {"price": 20, "quantity": 100}}
        )
=======
    def test_plan_next_travel_prefers_selling_inventory(self, agent_factory, city_factory):
        """AI should prioritize selling existing inventory for profit."""
        a = city_factory("A", connections=["B"])
        b = city_factory("B", fee=5, commodities={"item1": {"price": 20, "quantity": 100}})
>>>>>>> main
        cities = {"A": a, "B": b}

        agent = agent_factory(money=100, city="A")
        agent.inventory = {"item1": {"quantity": 10, "avg_buy_price": 10}}

        agent._plan_next_travel(cities)
        assert agent.travel_plan == ("B", None)

    def test_plan_next_travel_considers_buy_then_sell(self, agent_factory, city_factory):
        """AI should find profitable routes even with an empty inventory."""
<<<<<<< HEAD
        a = city_factory(
            "A",
            connections=["B"],
            commodities={"apple": {"price": 5, "quantity": 100}},
        )
        b = city_factory(
            "B", fee=10, commodities={"apple": {"price": 15, "quantity": 100}}
        )
=======
        a = city_factory("A", connections=["B"], commodities={"apple": {"price": 5, "quantity": 100}})
        b = city_factory("B", fee=10, commodities={"apple": {"price": 15, "quantity": 100}})
>>>>>>> main
        cities = {"A": a, "B": b}

        agent = agent_factory(money=1000, city="A")
        agent.inventory = {}

        agent._plan_next_travel(cities)
        assert agent.travel_plan == ("B", None)

<<<<<<< HEAD
    def test_plan_next_travel_picks_random_if_no_profit(
        self, agent_factory, city_factory, monkeypatch
    ):
        """If no profit is possible, AI should travel randomly."""
        a = city_factory("A", connections=["B", "C"])
        b = city_factory("B", fee=1000)  # Unprofitable
        c = city_factory("C", fee=1000)  # Unprofitable
        cities = {"A": a, "B": b, "C": c}

        agent = agent_factory(money=50, city="A")

=======
    def test_plan_next_travel_picks_random_if_no_profit(self, agent_factory, city_factory, monkeypatch):
        """If no profit is possible, AI should travel randomly."""
        a = city_factory("A", connections=["B", "C"])
        b = city_factory("B", fee=1000) # Unprofitable
        c = city_factory("C", fee=1000) # Unprofitable
        cities = {"A": a, "B": b, "C": c}

        agent = agent_factory(money=50, city="A")
        
>>>>>>> main
        # Force random.choice to be deterministic
        monkeypatch.setattr(random, "choice", lambda seq: "C")
        agent._plan_next_travel(cities)
        assert agent.travel_plan == ("C", None)

<<<<<<< HEAD
    def test_plan_next_travel_skips_missing_cities(
        self, agent_factory, city_factory, monkeypatch
    ):
        """AI should ignore connections to cities not present in the data."""
        a = city_factory("A", connections=["X", "B"])  # 'X' is not in cities
=======
    def test_plan_next_travel_skips_missing_cities(self, agent_factory, city_factory, monkeypatch):
        """AI should ignore connections to cities not present in the data."""
        a = city_factory("A", connections=["X", "B"]) # 'X' is not in cities
>>>>>>> main
        b = city_factory("B", fee=1000)
        cities = {"A": a, "B": b}

        agent = agent_factory(money=50, city="A")

        # random.choice should only be called with ['B']
        monkeypatch.setattr(random, "choice", lambda seq: seq[0])
        agent._plan_next_travel(cities)
        assert agent.travel_plan == ("B", None)
