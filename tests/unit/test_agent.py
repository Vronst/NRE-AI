"""Placeholder later to be removed."""

import pytest

from nre_ai.agent import AIAgent as agent

city: str = ''
agents: list = [
    agent(0, city),
    agent(10, city),
    agent(100, city),
    agent(-1, city),
    agent(1, city),
    agent(-100, city),
]

@pytest.mark.parametrize('agent', agents)
class TestAgentAI:  # noqa
    
    @pytest.mark.regression
    def test_bankruptcy(self, agent): #noqa
        if agent.money <= 0:
            assert agent.is_bankrupt()

