"""Gymnasium environment for the trading bot."""

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from nrecity import City
from nrecity.data_manager import JsonManager
from nrecity.data_processor import CityProcessor

from nre_ai.agent import AIAgent
from nre_ai.mechanics import (
    COMMODITIES,
    calculate_net_worth,
    execute_action,
    get_observation,
    sanitize_city_data,
)

# Constants
NUM_COMMODITIES = len(COMMODITIES)


class TradingEnv(gym.Env):
    """Custom Environment that follows gym interface."""

    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, cities_json_path: str):
        super().__init__()

        self.cities_json_path = cities_json_path
        self.json_manager = JsonManager(cities_json_path)
        self.city_processor = CityProcessor(self.json_manager)

        # Initialize state
        self.cities: dict[str, City] = {}
        self.agent: AIAgent | None = None
        self.city_names: list[str] = []
        self.current_step = 0
        self.max_steps = 1000

        # New counter for your logic
        self.steps_since_last_update = 0
        self.max_local_actions = 4  # Allow 4 buys/sells before forced update

        # Define Action Space
        # 0-4: Buy
        # 5-9: Sell
        # 10: Sell All
        # 11-20: Travel (Neighbors 0-9)
        self.action_space = spaces.Discrete(5 + 5 + 1 + 10)

        # Define Observation Space (37 inputs)
        self.observation_space = spaces.Box(low=0, high=1, shape=(37,), dtype=np.float32)

        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        # Sanitize data before processing to catch any lingering overflows
        if "after" in self.json_manager.data:
            sanitize_city_data(self.json_manager.data["after"])
        if "cities" in self.json_manager.data:
            sanitize_city_data(self.json_manager.data["cities"])

        self.city_processor.process_changes()
        self.cities = self.city_processor.get_dict_of_cities("after")
        self.city_names = list(self.cities.keys())

        start_city = self.city_names[0] if self.city_names else "Stolica"
        self.agent = AIAgent(name="TrainingBot", money=1000, initial_city=start_city)

        self.current_step = 0
        self.steps_since_last_update = 0
        self.prev_net_worth = 1000.0

        return get_observation(self.agent, self.cities), {}

    def step(self, action):
        self.current_step += 1
        self.steps_since_last_update += 1

        reward = 0
        terminated = False
        truncated = False
        info = {}

        # --- 1. Execute Action ---
        is_travel_action = execute_action(action, self.agent, self.cities)

        # --- 2. Conditional Economy Update ---
        # Update ONLY if we traveled OR if we hit the limit of local actions
        if is_travel_action or self.steps_since_last_update >= self.max_local_actions:
            self._sync_agent_changes_to_json_manager()

            # Sanitize the data in json_manager to prevent overflows in the submodule
            if "after" in self.json_manager.data:
                sanitize_city_data(self.json_manager.data["after"])

            self.city_processor.process_changes()
            self.cities = self.city_processor.get_dict_of_cities("after")
            self.steps_since_last_update = 0  # Reset counter

        # --- 3. Calculate Reward ---
        current_net_worth = calculate_net_worth(self.agent, self.cities)

        # Reward Scaling: Normalize by initial money or a fixed constant to keep rewards small
        # Instead of raw difference, use percentage growth or log difference
        # Here we use a scaled difference, but capped to avoid explosion
        reward = (current_net_worth - self.prev_net_worth) / 1000.0

        # Clip reward to [-10, 10] to prevent gradient explosion
        reward = max(min(reward, 10.0), -10.0)

        self.prev_net_worth = current_net_worth

        # Small penalty per step to encourage efficiency
        reward -= 0.001

        # --- 4. Checks ---
        if self.agent.money <= 0:
            terminated = True
            reward -= 10.0  # Bankruptcy

        # Stuck check
        min_fee = float("inf")
        # We need to re-fetch current city obj in case we traveled
        current_city_obj = self.cities[self.agent.current_city_name]
        for neighbor in current_city_obj.connections:
            if neighbor in self.cities:
                min_fee = min(min_fee, self.cities[neighbor].fee)

        if self.agent.money < min_fee and not self.agent.inventory:
            terminated = True
            reward -= 10.0  # Stuck

        if self.current_step >= self.max_steps:
            truncated = True

        return (
            get_observation(self.agent, self.cities),
            reward,
            terminated,
            truncated,
            info,
        )

    def _sync_agent_changes_to_json_manager(self):
        """Syncs the current state of self.cities back to the json_manager's data."""
        # The CityProcessor reads from self.json_manager.data["after"] (by default)
        # We need to update that list of dicts with the current values from self.cities

        target_list = self.json_manager.data.get("after", [])
        city_map = {c["name"]: c for c in target_list}

        for city_name, city_obj in self.cities.items():
            if city_name in city_map:
                city_dict = city_map[city_name]
                # Update commodities
                for item, details in city_obj.commodities.items():
                    # Check if details is None (which can happen based on City definition)
                    if details is None:
                        continue

                    if item in city_dict["commodities"]:
                        target_details = city_dict["commodities"][item]
                        # Check if target_details is None
                        if target_details is None:
                            continue

                        # Only update quantity as that's what the agent changes
                        target_details["quantity"] = details["quantity"]
