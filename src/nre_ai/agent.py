"""Base simple AI."""

import random

# it works trust me xd
from nrecity import City
from nrecity import factory as nrecity_factory_map

"""
Current issues:
- no forced move if nothing sold or bought
- insufficient sample data to check travel logic
- AI limits itself to one stock ATM
- NO TESTS!
"""


class AIAgent:
    """Represents the AI agent."""

    def __init__(
        self,
        name: str,
        money: int,
        initial_city: str,
        factory_map: dict | None = None,
    ):
        """Initializes the AI agent.

        Args:
            name (str): The unique name of the bot.
            money (int): Initial amount of money.
            initial_city (str): The name of the starting city.
            factory_map (dict | None): A map of commodities to factories.
                If None, uses the default from nrecity.
        """
        self.name = name
        self.money = money
        self.inventory = {}
        self.current_city_name = initial_city
        self.travel_plan = None
        self.factory_map = factory_map if factory_map is not None else nrecity_factory_map

    @classmethod
    def from_dict(cls, data: dict) -> "AIAgent":
        """Creates an AIAgent instance from a dictionary state.

        Args:
            data (dict): The dictionary containing bot state.

        Returns:
            AIAgent: The restored agent.
        """
        initial_city = data["current_city"]
        agent = cls(name=data["name"], money=data["zloto"], initial_city=initial_city)

        agent.inventory = data.get("inventory_full", {})

        return agent

    def to_dict(self) -> dict:
        """Exports the agent's state to a dictionary compatible with player.json.

        Returns:
            dict: The agent's state in the required format.
        """
        return {
            "name": self.name,
            "zloto": self.money,
            "current_city": self.current_city_name,
            "ekwipunek": {
                item: details["quantity"] for item, details in self.inventory.items()
            },
            "inventory_full": self.inventory,
        }

    def _is_produced_locally(self, city: City, item_name: str) -> bool:
        """Checks if a commodity is likely produced in the city."""
        if item_name in self.factory_map:
            return self.factory_map[item_name] in city.factory
        return False

    def take_turn(self, cities: dict[str, City]):
        """AI takes a turn, decides on actions."""
        # 1. Execute travel plan if any
        if self.travel_plan:
            destination_name = self.travel_plan[0]
            if destination_name in cities:
                fee = cities[destination_name].fee
                if self.money >= fee:
                    self.money -= fee
                    self.current_city_name = destination_name
                    print(
                        f"AI traveled to {self.current_city_name},"
                        f" paid {fee} fee. Money: {self.money}"
                    )
                else:
                    print(
                        f"AI cannot afford to travel to "
                        f"{self.current_city_name}. Cancelling travel."
                    )
            self.travel_plan = None  # Reset plan

        current_city = cities[self.current_city_name]

        # 2. Sell commodities
        self._sell_commodities(current_city)

        # 3. Buy commodities
        self._buy_commodities(current_city)

        # 4. Decide where to go next
        self._plan_next_travel(cities)

    def _sell_commodities(self, city: City):
        """Sells commodities in the current city if profitable."""
        commodities_to_sell = list(self.inventory.keys())
        for item_name in commodities_to_sell:
            if item_name in city.commodities and city.commodities[item_name]:
                market_price = city.commodities[item_name]["price"]
                avg_buy_price = self.inventory[item_name]["avg_buy_price"]

                # Sell if price is higher than average buy price + a 10% margin
                if market_price > avg_buy_price * 1.1:
                    quantity_to_sell = self.inventory[item_name]["quantity"]

                    # Ensure quantity exists before adding
                    if city.commodities[item_name]["quantity"] is None:
                        city.commodities[item_name]["quantity"] = 0

                    self.money += quantity_to_sell * market_price
                    city.commodities[item_name]["quantity"] += quantity_to_sell

                    print(
                        f"AI sold {quantity_to_sell} of {item_name} in "
                        f"{self.current_city_name} for {market_price}"
                        f" each. Money: {self.money}"
                    )

                    del self.inventory[item_name]

    def _buy_commodities(self, city: City):
        """Buys commodities in the current city.

        Prioritizing the best deals.
        """

        def acquire(item_name, details, price):
            """Helper function to purchase a commodity."""
            # Spend max 50% of *current* money on a single transaction
            # Ensure price is not zero to avoid division error
            if price <= 0:
                return False

            max_buy_by_money = int((self.money * 0.5) / price)

            # Ensure we don't try to buy more than is available
            quantity_to_buy = min(max_buy_by_money, details["quantity"])

            if quantity_to_buy > 0:
                self.money -= quantity_to_buy * price
                details["quantity"] -= quantity_to_buy

                if item_name not in self.inventory:
                    self.inventory[item_name] = {
                        "quantity": 0,
                        "avg_buy_price": 0,
                    }

                # Update average buy price
                current_quant = self.inventory[item_name]["quantity"]
                current_avg = self.inventory[item_name]["avg_buy_price"]
                new_total_cost = (current_quant * current_avg) + (quantity_to_buy * price)
                new_total_quant = current_quant + quantity_to_buy

                self.inventory[item_name]["avg_buy_price"] = (
                    new_total_cost / new_total_quant
                )
                self.inventory[item_name]["quantity"] += quantity_to_buy

                print(
                    f"AI bought {quantity_to_buy} of {item_name} in "
                    f"{self.current_city_name} for {price} each."
                    f" Money: {self.money}"
                )
                return True
            return False

        # 1. Identify all potential deals
        deals = []
        for item_name, details in city.commodities.items():
            if not details or details["quantity"] <= 0:
                continue

            price = details["price"]
            reg_price = details["regular_price"]

            # Skip if we can't afford even one
            if self.money < price or reg_price <= 0:
                continue

            is_produced_locally = self._is_produced_locally(city, item_name)
            discount_ratio = price / reg_price

            # Define "good deal" criteria
            # Priority 1: Locally produced and < 95% price, OR < 70% price
            is_good_deal = (is_produced_locally and discount_ratio < 0.95) or (
                discount_ratio < 0.7
            )
            # Priority 2: Any item just under regular price
            is_ok_deal = discount_ratio < 1.0

            if is_good_deal:
                deals.append(
                    {
                        "name": item_name,
                        "details": details,
                        "price": price,
                        "ratio": discount_ratio,
                        "priority": 1,
                    }
                )
            elif is_ok_deal:
                deals.append(
                    {
                        "name": item_name,
                        "details": details,
                        "price": price,
                        "ratio": discount_ratio,
                        "priority": 2,
                    }
                )

        # 2. Sort deals: priority 1 first, then by best ratio (lowest)
        deals.sort(key=lambda x: (x["priority"], x["ratio"]))

        # 3. Execute "good" and "ok" deals (Priority 1 and 2)
        for deal in deals:
            # Stop if we're low on cash
            if self.money < deal["price"]:
                continue

            acquire(deal["name"], deal["details"], deal["price"])

        # 4. If inventory is *still* empty, buy *anything* affordable
        # This checks inventory quantity, not just if we bought
        # something this turn
        is_inventory_empty = not any(
            info["quantity"] > 0 for info in self.inventory.values()
        )

        if is_inventory_empty:
            # Find the absolute cheapest item just to get started
            cheapest_item = None
            min_price = float("inf")

            for item_name, details in city.commodities.items():
                if (
                    details
                    and details["quantity"] > 0
                    and details["price"] < min_price
                    and self.money >= details["price"]
                ):
                    min_price = details["price"]
                    cheapest_item = (item_name, details)

            if cheapest_item:
                item_name, details = cheapest_item
                print(
                    f"AI has empty inventory, buying cheapest available item: {item_name}"
                )
                acquire(item_name, details, details["price"])

    def _plan_next_travel(self, cities: dict[str, City]):
        """Analyzes connected cities and plans the most profitable trip."""
        current_city = cities[self.current_city_name]
        best_profit = 0
        best_destination = None

        for destination_name in current_city.connections:
            if destination_name not in cities:
                continue

            destination_city = cities[destination_name]
            travel_fee = destination_city.fee

            # Check for best profit based on *current inventory*
            for item_name, inv_details in self.inventory.items():
                if (
                    inv_details["quantity"] > 0
                    # is check for destination_city.commodities
                    # necessary if citites uses the same
                    # schema?
                    and item_name in destination_city.commodities
                    and destination_city.commodities[item_name]
                ):
                    sell_price = destination_city.commodities[item_name]["price"]
                    avg_buy_price = inv_details["avg_buy_price"]
                    profit_per_unit = sell_price - avg_buy_price

                    # Estimate profit for whole stack, minus travel
                    potential_profit = (
                        profit_per_unit * inv_details["quantity"]
                    ) - travel_fee

                    if potential_profit > best_profit:
                        best_profit = potential_profit
                        best_destination = destination_name

            # If no inventory profit, check for *potential*
            # profit (buy here, sell there)
            if best_profit <= 0:
                for item_name, buy_details in current_city.commodities.items():
                    if (
                        not buy_details
                        or item_name not in destination_city.commodities
                        or not destination_city.commodities[item_name]
                    ):
                        continue

                    buy_price = buy_details["price"]
                    sell_price = destination_city.commodities[item_name]["price"]

                    profit_per_unit = sell_price - buy_price

                    if profit_per_unit > 0:
                        # Simple heuristic: assume we can transport 10 units
                        potential_profit = (profit_per_unit * 10) - travel_fee

                        if potential_profit > best_profit:
                            best_profit = potential_profit
                            best_destination = destination_name

        if best_destination and best_profit > 0:
            self.travel_plan = (best_destination, None)
            print(
                f"AI plans to travel to {best_destination} for"
                f" an estimated profit of {best_profit}."
            )
        else:
            if current_city.connections:
                # Filter out cities not present in the main dictionary
                valid_connections = [c for c in current_city.connections if c in cities]
                if valid_connections:
                    random_destination = random.choice(valid_connections)
                    self.travel_plan = (random_destination, None)
                    print(
                        f"AI has no profitable route, plans to travel"
                        f"randomly to {random_destination}."
                    )

    def is_bankrupt(self) -> bool:
        """Checks if the AI is bankrupt."""
        return self.money <= 0 and not self.inventory
