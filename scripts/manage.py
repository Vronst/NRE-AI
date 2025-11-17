"""Script to manage AI learning."""

import os

# import sys
# # Add src to python path to allow imports from sibling directories
# sys.path.insert(
#     0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# )
from data_processor.json_manager import JsonManager
from data_processor.processor import CityProcessor

from nre_ai.agent import AIAgent


def run_ai_simulation():
    """Runs the AI simulation for a number of turns."""
    # 1. Initialization
    json_path = os.getenv("CITY_PATH", None)
    if not json_path:
        raise KeyError("Path for json file with city data not provided")
    json_manager = JsonManager(json_path)
    processor = CityProcessor(json_manager)

    # TODO: wouldn't it be better to be random?
    # if so money should be adjusted
    # otherwise delete this
    # after -> because before is only for processor
    initial_cities = processor.get_dict_of_cities("after")
    initial_city_name = (
        list(initial_cities.keys())[0] if initial_cities else None
    )

    if not initial_city_name:
        print("Error: No cities found in data file.")
        return

    agent = AIAgent(money=1000, initial_city=initial_city_name)
    print(f"AI starts with {agent.money} money in {agent.current_city_name}.")

    # 2. Simulation Loop
    for turn in range(1, 101):
        print(f"\n--- Turn {turn} ---")

        # Reload data at the start of the turn
        json_manager(json_path)

        # Get current state of the world
        # ('after' and 'cities' are identical at this point)
        cities_state = processor.get_dict_of_cities("after")

        # AI takes its turn, modifying the city objects in `cities_state`
        agent.take_turn(cities_state)

        if agent.is_bankrupt():
            print("AI has gone bankrupt! Simulation over.")
            break

        # Update the 'after' data with the results of the AI's actions
        processor.json_manager.data["after"] = [
            c.to_dict() for c in cities_state.values()
        ]
        print(
            f"Has {agent.money:.2f} money.\nIs currently in "
            f"{agent.current_city_name}.\nCurrently possesses"
            f" {agent.inventory}.\n"
        )
        # Run the world processor. It will:
        # 1. Compare 'cities' (before AI) and 'after' (after AI).
        # 2. Calculate market changes based on the diff.
        # 3. Save the new state to both 'cities' and 'after' for the next turn.
        processor.process_changes()

        print(f"End of turn {turn}. AI has {agent.money:.2f} money.")

    print("\n--- Simulation Finished ---")
    print(
        f"Final AI state: Money = {agent.money:.2f},"
        f" Inventory = {agent.inventory}"
    )


if __name__ == "__main__":
    run_ai_simulation()
