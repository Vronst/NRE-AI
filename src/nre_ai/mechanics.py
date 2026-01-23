"""Shared mechanics for RL agent and environment."""

import numpy as np
from nrecity import City

# Constants
MAX_MONEY = 1000000.0
MAX_INVENTORY_QTY = 1000.0
MAX_PRICE = 1000.0
MAX_FEE = 1000.0
COMMODITIES = ["metal", "gems", "food", "fuel", "relics"]


def get_observation(agent, cities: dict[str, City]) -> np.ndarray:
    """Constructs the observation vector."""
    obs = []

    # 1. Agent Money (Normalized)
    obs.append(min(agent.money / MAX_MONEY, 1.0))

    # 2. Inventory (Normalized)
    for item in COMMODITIES:
        qty = 0
        if item in agent.inventory:
            qty = agent.inventory[item]["quantity"]
        obs.append(min(qty / MAX_INVENTORY_QTY, 1.0))

    # 3. Current City Data
    current_city = cities[agent.current_city_name]

    # Fee (Normalized)
    obs.append(min(current_city.fee / MAX_FEE, 1.0))

    # Prices and Quantities
    for item in COMMODITIES:
        details = current_city.commodities.get(item)
        if details:
            obs.append(min(details["price"] / MAX_PRICE, 1.0))
            obs.append(min(details["quantity"] / MAX_INVENTORY_QTY, 1.0))
        else:
            obs.append(0.0)
            obs.append(0.0)

    # 4. Connected Cities (Neighbors)
    neighbors = current_city.connections
    for i in range(10):
        if i < len(neighbors):
            neighbor_name = neighbors[i]
            if neighbor_name in cities:
                fee = cities[neighbor_name].fee
                obs.append(min(fee / MAX_FEE, 1.0))  # Fee
                obs.append(1.0)  # Connection exists
            else:
                obs.append(0.0)
                obs.append(0.0)
        else:
            obs.append(0.0)  # No connection
            obs.append(0.0)

    return np.array(obs, dtype=np.float32)


def execute_action(
    action: int, agent, cities: dict[str, City], verbose: bool = False
) -> bool:
    """Executes the given action.

    Args:
        action (int): The action index.
        agent: The agent instance.
        cities (dict[str, City]): The map of cities.
        verbose (bool): Whether to print action details.

    Returns:
        bool: True if the action resulted in travel, False otherwise.
    """
    current_city_obj = cities[agent.current_city_name]
    did_travel = False

    if action < 5:  # Buy
        item_idx = action
        item_name = COMMODITIES[item_idx]
        _execute_buy(agent, item_name, current_city_obj, verbose)
    elif action < 10:  # Sell
        item_idx = action - 5
        item_name = COMMODITIES[item_idx]
        _execute_sell(agent, item_name, current_city_obj, verbose)
    elif action == 10:  # Sell All
        _execute_sell_all(agent, current_city_obj, verbose)
    else:  # Travel
        neighbor_idx = action - 11
        did_travel = _execute_travel(
            agent, neighbor_idx, current_city_obj, cities, verbose
        )

    return did_travel


def _execute_buy(agent, item_name: str, city: City, verbose: bool):
    if item_name not in city.commodities or not city.commodities[item_name]:
        return

    details = city.commodities[item_name]
    price = details["price"]
    available_qty = details["quantity"]

    if available_qty <= 0:
        return

    amount_to_buy = 10
    max_can_afford = int(agent.money // price)
    amount_to_buy = min(amount_to_buy, max_can_afford, available_qty)

    if amount_to_buy > 0:
        cost = amount_to_buy * price
        agent.money -= cost

        if item_name not in agent.inventory:
            agent.inventory[item_name] = {"quantity": 0, "avg_buy_price": 0}

        current_qty = agent.inventory[item_name]["quantity"]
        current_avg = agent.inventory[item_name]["avg_buy_price"]

        new_total_cost = (current_qty * current_avg) + cost
        new_qty = current_qty + amount_to_buy
        agent.inventory[item_name]["quantity"] = new_qty
        agent.inventory[item_name]["avg_buy_price"] = new_total_cost / new_qty

        details["quantity"] -= amount_to_buy
        if verbose:
            print(f"{agent.name} bought {amount_to_buy} {item_name} for {cost}")


def _execute_sell(agent, item_name: str, city: City, verbose: bool):
    if item_name not in agent.inventory:
        return

    qty = agent.inventory[item_name]["quantity"]
    if qty <= 0:
        return

    if item_name not in city.commodities or not city.commodities[item_name]:
        return

    price = city.commodities[item_name]["price"]
    amount_to_sell = min(10, qty)

    revenue = amount_to_sell * price
    agent.money += revenue

    # Cap money to prevent explosion
    if agent.money > MAX_MONEY:
        agent.money = MAX_MONEY

    agent.inventory[item_name]["quantity"] -= amount_to_sell
    if agent.inventory[item_name]["quantity"] <= 0:
        del agent.inventory[item_name]

    city.commodities[item_name]["quantity"] += amount_to_sell

    # Cap city quantity to prevent explosion
    if city.commodities[item_name]["quantity"] > MAX_INVENTORY_QTY:
        city.commodities[item_name]["quantity"] = int(MAX_INVENTORY_QTY)

    if verbose:
        print(f"{agent.name} sold {amount_to_sell} {item_name} for {revenue}")


def _execute_sell_all(agent, city: City, verbose: bool):
    items = list(agent.inventory.keys())
    for item in items:
        if item not in city.commodities or not city.commodities[item]:
            continue

        price = city.commodities[item]["price"]
        qty = agent.inventory[item]["quantity"]

        revenue = qty * price
        agent.money += revenue
        del agent.inventory[item]

        city.commodities[item]["quantity"] += qty

        # Cap city quantity to prevent explosion
        if city.commodities[item]["quantity"] > MAX_INVENTORY_QTY:
            city.commodities[item]["quantity"] = int(MAX_INVENTORY_QTY)

        if verbose:
            print(f"{agent.name} sold all {qty} {item} for {revenue}")

    # Cap money to prevent explosion
    if agent.money > MAX_MONEY:
        agent.money = MAX_MONEY


def _execute_travel(
    agent, neighbor_idx: int, city: City, cities: dict[str, City], verbose: bool
) -> bool:
    neighbors = city.connections
    if neighbor_idx >= len(neighbors):
        return False

    target_city_name = neighbors[neighbor_idx]
    if target_city_name not in cities:
        return False

    target_city = cities[target_city_name]
    fee = target_city.fee

    if agent.money >= fee:
        agent.money -= fee
        agent.current_city_name = target_city_name
        if verbose:
            print(f"{agent.name} traveled to {target_city_name} (fee: {fee})")
        return True

    return False


def calculate_net_worth(agent, cities: dict[str, City]) -> float:
    """Calculates the total net worth of the agent."""
    value = agent.money
    current_city = cities[agent.current_city_name]
    for item, details in agent.inventory.items():
        qty = details["quantity"]
        price = 0
        if item in current_city.commodities and current_city.commodities[item]:
            raw_price = current_city.commodities[item]["price"]
            # Cap price to prevent valuation explosion during hyperinflation
            price = min(raw_price, MAX_PRICE)
        value += qty * price
    return value


def sanitize_city_data(city_data_list: list[dict]):
    """Clamps prices and quantities in the raw city data to prevent overflows.

    Args:
        city_data_list (list[dict]): The list of city dictionaries from JsonManager.
    """
    for city_data in city_data_list:
        if "commodities" not in city_data:
            continue

        for item_name, details in city_data["commodities"].items():
            if not details:
                continue

            # Clamp Price
            if details.get("price", 0) > MAX_PRICE:
                details["price"] = int(MAX_PRICE)
            if details.get("regular_price", 0) > MAX_PRICE:
                details["regular_price"] = int(MAX_PRICE)

            # Clamp Quantity
            if details.get("quantity", 0) > MAX_INVENTORY_QTY:
                details["quantity"] = int(MAX_INVENTORY_QTY)
            if details.get("regular_quantity", 0) > MAX_INVENTORY_QTY:
                details["regular_quantity"] = int(MAX_INVENTORY_QTY)
