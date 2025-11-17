# noqa: D100
# import json

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


class TestAgentAI:  # noqa
    @pytest.mark.parametrize("agent", agents)
    def test_bankruptcy(self, agent):  # noqa
        if agent.money <= 0:
            assert agent.is_bankrupt()

    @pytest.mark.regression
    @pytest.mark.parametrize("agent", agents)
    def test_is_produced_locally(  # noqa
        self,  # noqa
        agent,
        mock_city_all,
        mock_city_no_factory,
    ):
        factory = list(factory_map.keys())[0]
        assert not agent._is_produced_locally(mock_city_no_factory, factory)
        assert agent._is_produced_locally(mock_city_all, factory)
