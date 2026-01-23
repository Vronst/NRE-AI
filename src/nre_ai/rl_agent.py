"""RL Agent wrapper for the trading bot."""

from nrecity import City
from stable_baselines3 import PPO

from nre_ai.agent import AIAgent
from nre_ai.mechanics import execute_action, get_observation


class RLAgent(AIAgent):
    """RL-based Agent that wraps the rule-based AIAgent structure."""

    def __init__(self, name: str, money: int, initial_city: str, model_path: str):
        super().__init__(name, money, initial_city)
        self.model = PPO.load(model_path)
        self.model_path = model_path

    @classmethod
    def from_dict(cls, data: dict) -> "RLAgent":
        """Creates an RL agent instance from a dictionary state."""
        initial_city = data["current_city"]
        model_path = data.get("model_path")
        if not model_path:
            raise ValueError("RLAgent requires 'model_path' in the data dictionary.")

        agent = cls(
            name=data["name"],
            money=data["zloto"],
            initial_city=initial_city,
            model_path=model_path,
        )
        agent.inventory = data.get("inventory_full", {})
        return agent

    def to_dict(self) -> dict:
        """Exports the agent's state to a dictionary, including model_path."""
        data = super().to_dict()
        data["model_path"] = self.model_path
        return data

    def take_turn(self, cities: dict[str, City]):
        """Uses the RL model to decide on an action."""
        # 1. Construct Observation
        obs = get_observation(self, cities)

        # 2. Predict Action
        action, _states = self.model.predict(obs, deterministic=True)

        # 3. Execute Action
        execute_action(action, self, cities, verbose=True)
