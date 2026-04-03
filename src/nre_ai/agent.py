"""Base simple bots."""

from nrecity import City
from nrecity import factory as nrecity_factory_map

# Constants
ITEM_WEIGHTS = {
    "gems": 1.0,
    "food": 2.0,
    "fuel": 3.0,
    "metal": 5.0,
    "relics": 10.0,
}
MAX_WEIGHT = 1000.0


class AIAgent:
    """Represents the bot."""

    def __init__(
        self,
        name: str,
        money: int,
        initial_city: str,
        factory_map: dict | None = None,
    ):
        """Initializes the bot.

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
        """Creates a bot instance from a dictionary state.

        Args:
            data (dict): The dictionary containing bot state.

        Returns:
            Bot: The restored bot.
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

    def _get_item_weight(self, item_name: str) -> float:
        """Returns the weight of a single unit of the item."""
        return ITEM_WEIGHTS.get(item_name.lower(), 1.0)

    def _calculate_current_weight(self) -> float:
        """Calculates the total weight of the inventory."""
        total_weight = 0.0
        for item_name, details in self.inventory.items():
            total_weight += details["quantity"] * self._get_item_weight(item_name)
        return total_weight

    def _is_produced_locally(self, city: City, item_name: str) -> bool:
        """Checks if a commodity is likely produced in the city."""
        if item_name in self.factory_map:
            return self.factory_map[item_name] in city.factory
        return False

    def take_turn(self, cities: dict[str, City]):
        """Bot takes a turn, decides on actions."""
        # 1. Execute Travel
        if self.travel_plan:
            destination_name = self.travel_plan[0]
            if destination_name in cities:
                fee = cities[destination_name].fee
                if self.money >= fee:
                    self.money -= fee
                    self.current_city_name = destination_name
                    print(
                        f"Bot traveled to {self.current_city_name},"
                        f" paid {fee} fee. Money: {self.money}"
                    )
                else:
                    print(
                        f"Bot cannot afford to travel to "
                        f"{destination_name}. Cancelling travel."
                    )
                    self.travel_plan = None
            else:
                self.travel_plan = None

        current_city = cities[self.current_city_name]

        # 2. Sell
        self._sell_commodities(current_city)

        # 3. Plan & Buy
        has_inventory = any(item["quantity"] > 0 for item in self.inventory.values())

        if has_inventory:
            self._plan_with_inventory(current_city, cities)
        else:
            self._plan_and_buy_empty_inventory(current_city, cities)

    def _sell_commodities(self, city: City):
        """Sells commodities in the current city if profitable or high demand."""
        commodities_to_sell = list(self.inventory.keys())
        for item_name in commodities_to_sell:
            if item_name not in city.commodities or not city.commodities[item_name]:
                continue

            details = city.commodities[item_name]
            market_price = details["price"]
            avg_buy_price = self.inventory[item_name]["avg_buy_price"]

            # Scarcity check
            regular_quantity = details.get("regular_quantity", 100)
            city_quantity = details["quantity"]
            is_scarce = city_quantity < 0.1 * regular_quantity

            # Sell condition
            if (market_price > avg_buy_price * 1.1) or is_scarce:
                quantity_to_sell = self.inventory[item_name]["quantity"]

                if details["quantity"] is None:
                    details["quantity"] = 0

                self.money += quantity_to_sell * market_price
                details["quantity"] += quantity_to_sell

                print(
                    f"Bot sold {quantity_to_sell} of {item_name} in "
                    f"{self.current_city_name} for {market_price}"
                    f" each. Money: {self.money}"
                )

                del self.inventory[item_name]

    def _plan_with_inventory(self, current_city: City, cities: dict[str, City]):
        """Plans travel when holding inventory."""
        best_profit = float("-inf")
        best_destination = None

        # Scan neighbors
        for neighbor_name in current_city.connections:
            if neighbor_name not in cities or neighbor_name == self.current_city_name:
                continue

            neighbor_city = cities[neighbor_name]
            fee = neighbor_city.fee

            total_potential_profit = 0

            for item_name, inv_details in self.inventory.items():
                if (
                    item_name in neighbor_city.commodities
                    and neighbor_city.commodities[item_name]
                ):
                    sell_price = neighbor_city.commodities[item_name]["price"]
                    avg_buy_price = inv_details["avg_buy_price"]
                    quantity = inv_details["quantity"]

                    profit = (sell_price - avg_buy_price) * quantity
                    total_potential_profit += profit

            total_potential_profit -= fee

            if total_potential_profit > best_profit:
                best_profit = total_potential_profit
                best_destination = neighbor_name

        if best_destination and best_profit > 0:
            self.travel_plan = (best_destination, None)
            print(
                f"Bot plans to travel to {best_destination} to sell inventory. "
                f"Est profit: {best_profit}"
            )
        else:
            self._fallback_travel(current_city, cities)

    def _find_best_trade(
        self, current_city: City, cities: dict[str, City], only_local: bool
    ):
        """Finds the best trade available in the current city."""
        best_trade = None  # (profit, item_name, destination, count, buy_price)
        current_weight = self._calculate_current_weight()

        for item_name, details in current_city.commodities.items():
            if not details or details["quantity"] <= 0:
                continue

            # Filter: Produced locally or Relics if only_local is True
            if only_local and not (
                self._is_produced_locally(current_city, item_name)
                or item_name == "relics"
            ):
                continue

            buy_price = details["price"]
            item_weight = self._get_item_weight(item_name)

            # Simulate Trade with neighbors
            for neighbor_name in current_city.connections:
                if neighbor_name not in cities or neighbor_name == self.current_city_name:
                    continue

                neighbor_city = cities[neighbor_name]
                fee = neighbor_city.fee

                # Scarcity Heuristic
                neighbor_details = neighbor_city.commodities.get(item_name)
                if not neighbor_details:
                    continue

                regular_price = neighbor_details.get("regular_price", buy_price)
                regular_quantity = neighbor_details.get("regular_quantity", 100)
                neighbor_quantity = neighbor_details.get("quantity", 0)
                current_neighbor_price = neighbor_details.get("price", 0)

                if neighbor_quantity < 0.1 * regular_quantity:
                    est_sell_price = regular_price * 1.5
                else:
                    est_sell_price = regular_price * 0.8

                # Update: Set est_sell_price = max(est_sell_price, current_neighbor_price)
                est_sell_price = max(est_sell_price, current_neighbor_price)

                # Constraints
                # Money: reserve fee AND a small buffer.
                buffer = 10
                available_money = self.money - fee - buffer
                if available_money <= 0:
                    continue

                max_count_money = int(available_money / buy_price)

                # Weight
                available_weight = MAX_WEIGHT - current_weight
                if available_weight <= 0:
                    continue
                max_count_weight = int(available_weight / item_weight)

                # Supply
                max_count_supply = details["quantity"]

                count = max(0, min(max_count_money, max_count_weight, max_count_supply))

                if count <= 0:
                    continue

                profit = (est_sell_price - buy_price) * count - fee

                if best_trade is None or profit > best_trade[0]:
                    best_trade = (
                        profit,
                        item_name,
                        neighbor_name,
                        count,
                        buy_price,
                    )
        return best_trade

    def _plan_and_buy_empty_inventory(self, current_city: City, cities: dict[str, City]):
        """Plans trade and buys goods when inventory is empty."""
        # First Pass: Prioritize high-margin trades (local production)
        best_trade = self._find_best_trade(current_city, cities, only_local=True)

        # Second Pass: If no valid trade is found, consider all commodities
        if not best_trade or best_trade[0] <= 0:
            best_trade = self._find_best_trade(current_city, cities, only_local=False)

        if best_trade and best_trade[0] > 0:
            profit, item_name, destination, count, buy_price = best_trade

            # Execute Buy
            self.money -= count * buy_price
            current_city.commodities[item_name]["quantity"] -= count

            if item_name not in self.inventory:
                self.inventory[item_name] = {"quantity": 0, "avg_buy_price": 0}

            # Update inventory
            self.inventory[item_name]["quantity"] = count
            self.inventory[item_name]["avg_buy_price"] = buy_price

            print(
                f"Bot bought {count} of {item_name} for {buy_price} each. "
                f"Est profit: {profit}"
            )

            # Set travel plan
            self.travel_plan = (destination, None)
            print(f"Bot plans to travel to {destination}.")

        else:
            self._fallback_travel(current_city, cities)

    def _fallback_travel(self, current_city: City, cities: dict[str, City]):
        """Sets travel plan to the cheapest neighbor."""
        best_neighbor = None
        min_fee = float("inf")

        for neighbor_name in current_city.connections:
            if neighbor_name in cities and neighbor_name != self.current_city_name:
                fee = cities[neighbor_name].fee
                if fee < min_fee:
                    min_fee = fee
                    best_neighbor = neighbor_name

        if best_neighbor:
            self.travel_plan = (best_neighbor, None)
            print(f"Bot fallback: plans to travel to {best_neighbor} (lowest fee).")
        else:
            print("Bot stuck: no connections.")

    def is_bankrupt(self) -> bool:
        """Checks if the bot is bankrupt."""
        return self.money <= 0 and not self.inventory
