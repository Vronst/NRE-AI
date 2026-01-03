"""
Custom OpenAI Gym/Gymnasium environment for the NRE game.
"""
import json
import random
from typing import Dict, Any, Optional, Tuple, List

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from nre_ai.agent import AIAgent
from nrecity import City, factory as nrecity_factory_map, CityProcessor, JsonManager

# Constants
MAX_CITIES = 40  # Increased to accommodate larger maps
MAX_COMMODITIES = 6
MAX_CONNECTIONS = 5
MAX_HISTORY_LEN = 20


class GameTradingEnv(gym.Env):
    """
    A custom environment for training an RL agent on the game's trading mechanics.
    It simulates the game loop and provides the necessary components for an RL agent
    to learn how to maximize profit.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, cities_data_path: str, initial_money: int = 1000, start_city: str = "Stolica"):
        """
        Initializes the game environment.

        Args:
            cities_data_path (str): Path to the JSON file containing city data.
            initial_money (int): The base starting money (will be randomized).
            start_city (str): The default starting city (will be randomized).
        """
        super().__init__()

        self.cities_data_path = cities_data_path
        self.initial_money = initial_money
        self.start_city = start_city

        # Load initial data for resetting the environment to a clean state
        with open(cities_data_path, 'r') as f:
            self.initial_json_data = json.load(f)

        # Initialize processor and load cities
        self.json_manager = JsonManager(cities_data_path)
        self.processor = CityProcessor(self.json_manager)
        self.cities = self.processor.get_dict_of_cities("after")

        # Setup maps
        self.city_map = {name: i for i, name in enumerate(self.cities.keys())}
        
        # Assuming commodities are consistent across cities
        first_city_commodities = next(iter(self.cities.values())).commodities.keys()
        self.commodity_map = {name: i for i, name in enumerate(first_city_commodities)}

        # Define the action space
        # Action space: 0=wait, 1-6=sell, 7-12=buy, 13-17=travel
        self.action_space = spaces.Discrete(1 + MAX_COMMODITIES + MAX_COMMODITIES + MAX_CONNECTIONS)

        # Define the observation space
        self.observation_space = spaces.Dict({
            "money": spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32),
            "city_index": spaces.Discrete(MAX_CITIES),
            "inventory_quantities": spaces.Box(low=0, high=np.inf, shape=(MAX_COMMODITIES,), dtype=np.float32),
            "inventory_avg_prices": spaces.Box(low=0, high=np.inf, shape=(MAX_COMMODITIES,), dtype=np.float32),
            "market_quantities": spaces.Box(low=0, high=np.inf, shape=(MAX_COMMODITIES,), dtype=np.float32),
            "market_prices": spaces.Box(low=0, high=np.inf, shape=(MAX_COMMODITIES,), dtype=np.float32),
            "visited_cities_history": spaces.Box(low=0, high=MAX_CITIES, shape=(MAX_HISTORY_LEN,), dtype=np.int32),
            "inventory_utilization": spaces.Box(low=0, high=1.0, shape=(1,), dtype=np.float32),
        })

        # Initialize the agent
        self.agent = self._create_agent()
        
        # Stuck detection
        self.recent_actions = []
        self.max_history = 20
        self.turns_without_action = 0

    def _create_agent(self) -> AIAgent:
        """Creates a new AI agent for the environment with randomized start."""
        # Randomize start city from available cities
        start_city = random.choice(list(self.cities.keys()))
        
        # Randomize money (e.g., +/- 50% of initial_money)
        # If initial_money is 1000, range is 500-1500
        low = int(self.initial_money * 0.5)
        high = int(self.initial_money * 1.5)
        money = random.randint(low, high)

        return AIAgent(
            name="RL_Bot",
            money=money,
            initial_city=start_city,
            factory_map=nrecity_factory_map,
        )

    def _get_observation(self) -> Dict[str, Any]:
        """Constructs the observation dictionary from the current game state."""
        return get_observation_from_state(self.agent, self.cities, self.city_map, self.commodity_map)

    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Resets the environment to its initial state."""
        super().reset(seed=seed)
        
        # Restore file to initial state to ensure episode independence
        with open(self.cities_data_path, 'w') as f:
            json.dump(self.initial_json_data, f)
            
        # Re-initialize processor/manager to pick up fresh file
        self.json_manager = JsonManager(self.cities_data_path)
        self.processor = CityProcessor(self.json_manager)
        self.cities = self.processor.get_dict_of_cities("after")
        
        # Reset agent with randomized state
        self.agent = self._create_agent()
        
        # Reset stuck detection
        self.recent_actions = []
        self.turns_without_action = 0
        
        return self._get_observation(), {}

    def step(self, action: int) -> Tuple[Dict[str, Any], float, bool, bool, Dict[str, Any]]:
        """
        Executes one step in the environment.

        Args:
            action (int): The action to perform.

        Returns:
            A tuple containing the new observation, reward, terminated flag, truncated flag, and info dict.
        """
        prev_money = self.agent.money
        reward = 0
        terminated = False
        truncated = False
        info = {}

        # --- Action Interpretation & Immediate Reward ---
        
        # Apply a small, default step penalty to every action to encourage efficiency.
        reward -= 0.1

        commodity_map_keys = list(self.commodity_map.keys())
        action_result = perform_action(self.agent, self.cities, commodity_map_keys, action)
        
        # --- World Evolution (CityProcessor) ---
        # Sync changes made by agent to the processor's data
        self.processor.json_manager.data["after"] = [c.to_dict() for c in self.cities.values()]
        
        # Run the world processor to simulate market changes
        self.processor.process_changes()
        
        # Update local cities state from the processor's output
        self.cities = self.processor.get_dict_of_cities("after")
        
        # --- Reward Shaping ---
        
        # 1. Stagnation Penalty (Boredom)
        if action == 0: # Wait action
            self.turns_without_action += 1
            reward -= 1.0 * self.turns_without_action # Increasing penalty for waiting
        else:
            self.turns_without_action = 0
            
        if not action_result:
             reward -= 5 # Penalty for invalid action

        # 2. Market Mover Bonus (Volume)
        # Check if action was buy or sell
        is_sell = 1 <= action <= MAX_COMMODITIES
        is_buy = MAX_COMMODITIES < action <= 2 * MAX_COMMODITIES
        
        if action_result and (is_sell or is_buy):
            # Reward for transaction volume regardless of profit
            # We can approximate volume by money change magnitude
            money_diff = abs(self.agent.money - prev_money)
            reward += money_diff * 0.01 # 1% of transaction value as bonus

        # 3. Risk/Courage Reward (Big Bets)
        if action_result and is_buy:
             money_spent = prev_money - self.agent.money
             if prev_money > 0:
                 spend_ratio = money_spent / prev_money
                 if spend_ratio > 0.4: # Spent more than 40% of cash
                     reward += 10.0 # Bonus for courage

        # 4. Nomad Bonus (Travel)
        is_travel = 2 * MAX_COMMODITIES < action
        if action_result and is_travel:
            # Reward for visiting a new city (or one not visited recently)
            # The agent.visited_cities_history is updated in perform_action/agent logic
            # We check if the new city was recently visited
            current_city = self.agent.current_city_name
            # Count occurrences in recent history (excluding the just added one)
            recent_visits = self.agent.visited_cities_history[:-1].count(current_city)
            
            if recent_visits == 0:
                reward += 15.0 # Big bonus for new/rarely visited city
            elif recent_visits < 3:
                reward += 5.0 # Small bonus
            else:
                reward -= 5.0 # Penalty for backtracking too much

        # --- Calculate Profit/Loss Reward ---
        # We still want profit, but it's not the ONLY thing
        profit = self.agent.money - prev_money
        reward += profit * 0.001 # Scaled down profit reward

        # --- Stuck & Bankruptcy Detection ---
        if self.agent.is_bankrupt():
            terminated = True
            reward -= 1000
        else:
            self.recent_actions.append(action)
            if len(self.recent_actions) > self.max_history:
                self.recent_actions.pop(0)
            
            if self._detect_loop():
                reward -= 50 # Overwrite with a large penalty
                truncated = True
                info["stuck"] = True

        return self._get_observation(), reward, terminated, truncated, info

    def _detect_loop(self) -> bool:
        """
        Detects if the agent is stuck in a simple loop.
        Checks for:
        - Repeating the same action 6 times.
        - Repeating the same 2-action sequence 3 times (e.g., A,B,A,B,A,B).
        - Repeating the same 3-action sequence 3 times (e.g., A,B,C,A,B,C,A,B,C).
        """
        n = len(self.recent_actions)

        # Check for single action repetition (e.g., A,A,A,A,A,A)
        if n >= 6 and all(a == self.recent_actions[-1] for a in self.recent_actions[-6:]):
            return True

        # Check for 2-action pattern repetition (e.g., A,B,A,B,A,B)
        if n >= 6:
            p1 = self.recent_actions[-2:]
            p2 = self.recent_actions[-4:-2]
            p3 = self.recent_actions[-6:-4]
            if p1 == p2 and p2 == p3:
                return True
        
        # Check for 3-action pattern repetition (e.g., A,B,C,A,B,C,A,B,C)
        if n >= 9:
            p1 = self.recent_actions[-3:]
            p2 = self.recent_actions[-6:-3]
            p3 = self.recent_actions[-9:-6]
            if p1 == p2 and p2 == p3:
                return True

        return False

    def render(self, mode="human"):
        """Renders the environment state."""
        if mode == "human":
            print(f"Money: {self.agent.money}, City: {self.agent.current_city_name}")
            print(f"Inventory: {self.agent.inventory}")
            print("-" * 20)

    def close(self):
        """Cleans up the environment."""
        pass

# Helper functions to be shared with RLAgent
def get_observation_from_state(agent: AIAgent, cities: Dict[str, City], city_map: Dict[str, int], commodity_map: Dict[str, int]) -> Dict[str, Any]:
    obs = {
        "money": np.array([agent.money], dtype=np.float32),
        "city_index": city_map[agent.current_city_name],
        "inventory_quantities": np.zeros(MAX_COMMODITIES, dtype=np.float32),
        "inventory_avg_prices": np.zeros(MAX_COMMODITIES, dtype=np.float32),
        "market_quantities": np.zeros(MAX_COMMODITIES, dtype=np.float32),
        "market_prices": np.zeros(MAX_COMMODITIES, dtype=np.float32),
        "visited_cities_history": np.zeros(MAX_HISTORY_LEN, dtype=np.int32),
        "inventory_utilization": np.array([0.0], dtype=np.float32),
    }

    total_items = 0
    for item, details in agent.inventory.items():
        if item in commodity_map:
            idx = commodity_map[item]
            obs["inventory_quantities"][idx] = details["quantity"]
            obs["inventory_avg_prices"][idx] = details["avg_buy_price"]
            total_items += details["quantity"]
            
    # Simple utilization metric (assuming max capacity isn't strictly defined but we want to track load)
    # Let's normalize by an arbitrary "large" load like 100 items
    obs["inventory_utilization"][0] = min(total_items / 100.0, 1.0)

    current_city = cities[agent.current_city_name]
    for item, details in current_city.commodities.items():
        if item in commodity_map and details:
            idx = commodity_map[item]
            obs["market_quantities"][idx] = details["quantity"]
            obs["market_prices"][idx] = details["price"]
            
    # Fill history buffer
    # We take the last N visited cities, map them to indices, and pad with -1 or 0
    history_len = len(agent.visited_cities_history)
    start_idx = max(0, history_len - MAX_HISTORY_LEN)
    recent_history = agent.visited_cities_history[start_idx:]
    
    for i, city_name in enumerate(recent_history):
        if city_name in city_map:
            obs["visited_cities_history"][i] = city_map[city_name]
    
    return obs

def perform_action(agent: AIAgent, cities: Dict[str, City], commodity_map_keys: List[str], action: int) -> bool:
    """
    Executes the action on the agent and cities.
    Returns True if the action was valid/successful, False otherwise.
    """
    current_city = cities[agent.current_city_name]
    
    # Wait
    if action == 0:
        return True
    
    # Sell actions
    elif 1 <= action <= MAX_COMMODITIES:
        commodity_name = commodity_map_keys[action - 1]
        return agent.sell_commodity(current_city, commodity_name)

    # Buy actions
    elif MAX_COMMODITIES < action <= 2 * MAX_COMMODITIES:
        commodity_name = commodity_map_keys[action - 1 - MAX_COMMODITIES]
        return agent.buy_commodity(current_city, commodity_name)

    # Travel actions
    elif 2 * MAX_COMMODITIES < action:
        connection_index = action - (2 * MAX_COMMODITIES + 1)
        connections = current_city.connections
        if connection_index < len(connections):
            destination = connections[connection_index]
            agent.travel_plan = (destination, None)
            
            # Execute travel immediately
            if destination in cities:
                fee = cities[destination].fee
                if agent.money >= fee:
                    agent.money -= fee
                    agent.current_city_name = destination
                    agent.travel_plan = None
                    
                    # Update history
                    agent.visited_cities_history.append(destination)
                    if len(agent.visited_cities_history) > MAX_HISTORY_LEN:
                         agent.visited_cities_history.pop(0)

                    return True
    
    return False
