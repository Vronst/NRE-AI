# noqa: D100
# import json

import random

import pytest
from data_processor.processor import factory as factory_map

from nre_ai.agent import AIAgent as Agent

# with open('../test_city_data.json') as file:
#     data = json.load(file)

# city: str = data['after'][0]['name']
city: str = "none"
agents: list = [
    Agent(0, city),
    Agent(10, city),
    Agent(100, city),
    Agent(-1, city),
    Agent(1, city),
    Agent(-100, city),
]


class TestAgentAIBankruptcy:  # noqa
        
    @pytest.mark.parametrize("agent", agents)
    def test_bankruptcy(self, agent):  # noqa
        if agent.money <= 0:
            assert agent.is_bankrupt()

class TestAgentAIIsProducedLocaly:  # noqa

    @pytest.mark.regression
    @pytest.mark.parametrize("agent", agents)
    def test_is_produced_locally(  # noqa
        self,  # noqa
        agent,
        city_factory
    ):
        
        no_factories = city_factory(factory=[])
        all_factories = city_factory(factory=list(factory_map.values()))
        factory = list(factory_map.keys())[0]
        assert not agent._is_produced_locally(no_factories, factory)
        assert agent._is_produced_locally(all_factories, factory)


class TestAgentAIPlanNextTravel:  # noqa

    def test_plan_next_travel_prefers_selling_inventory(self, city_factory):  # noqa
        a = city_factory("A", connections=["B"], commodities={})
        b = city_factory("B", fee=5,
                         commodities={"apple": {"price": 20, "quantity": 100}})

        cities = {"A": a, "B": b}

        agent = Agent(money=0, initial_city='A')
        # Give agent inventory with profit if sold in B
        agent.inventory = {"item1": {"quantity": 10, "avg_buy_price": 10}}

        agent._plan_next_travel(cities)

        assert agent.travel_plan == ("B", None)


    def test_plan_next_travel_considers_buy_then_sell_potential(  # noqa
        self, city_factory):
        a = city_factory("A", connections=["B"],
                         commodities={"apple": {"price": 5, "quantity": 100}})
        b = city_factory("B", fee=10,
                         commodities={"apple": {"price": 15, "quantity": 100}})

        cities = {"A": a, "B": b}

        agent = Agent(money=1000, initial_city="A")
        agent.inventory = {}  # empty inventory

        agent._plan_next_travel(cities)

        assert agent.travel_plan == ("B", None)


    def test_plan_next_travel_picks_random_connection_when_no_profit(  # noqa
        self,
        city_factory,
        monkeypatch):
        # No profitable opportunities;
        # ensure random.choice is used for determinism.
        a = city_factory("A", connections=["B", "C"], commodities={})
        b = city_factory("B", fee=1000, commodities={})
        c = city_factory("C", fee=1000, commodities={})

        cities = {"A": a, "B": b, "C": c}

        agent = Agent(money=50, initial_city="A")
        agent.inventory = {}

        # Force random.choice to pick 'C'
        monkeypatch.setattr(random, "choice", lambda seq: "C")

        agent._plan_next_travel(cities)

        assert agent.travel_plan == ("C", None)


    def test_plan_next_travel_skips_missing_cities(self,  # noqa
                                                   city_factory,
                                                   monkeypatch):
        # Connections include a missing city 'X' which should be ignored.
        a = city_factory("A", connections=["X", "B"], commodities={})
        b = city_factory("B", fee=1000, commodities={})

        cities = {"A": a, "B": b}

        agent = Agent(money=50, initial_city="A")
        agent.inventory = {}

        # With no profit, pick the only valid connection 'B'
        monkeypatch.setattr(random, "choice", lambda seq: seq[0])

        agent._plan_next_travel(cities)

        assert agent.travel_plan == ("B", None)
