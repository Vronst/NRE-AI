"""Script to manage AI learning."""

import os

from nrecity import CityProcessor, JsonManager

from nre_ai.agent import AIAgent, RLAgent


def run_ai_simulation():
    """Runs the AI simulation for a number of turns."""
    # 1. Initialization
    json_path = os.getenv("DATA_PATH", None)
    if not json_path:
        raise KeyError("Path for json file with city data not provided")
    json_manager = JsonManager(json_path + "miasta.json")
    processor = CityProcessor(json_manager)

    # TODO: wouldn't it be better to be random?
    # if so money should be adjusted
    # otherwise delete this
    # after -> because before is only for processor
    initial_cities = processor.get_dict_of_cities("after")
    initial_city_name = list(initial_cities.keys())[0] if initial_cities else None

    if not initial_city_name:
        print("Error: No cities found in data file.")
        return

    # --- Agent Setup ---
    # Determine paths relative to the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    model_path = os.path.join(project_root, "models", "nre_ppo_bot.zip")
    cities_static_path = os.path.join(project_root, "submodules", "NRE", "Assets", "Data", "Save", "miasta.json")

    if os.path.exists(model_path) and os.path.exists(cities_static_path):
        print(f"Found trained model at: {model_path}")
        agent = RLAgent(
            name="RL_Bot",
            money=1000,
            initial_city=initial_city_name,
            model_path=model_path,
            cities_data_path=cities_static_path
        )
    else:
        print("Trained model not found. Using default Rule-Based Agent.")
        agent = AIAgent(name="Simple_Bot", money=1000, initial_city=initial_city_name)

    print(f"Agent '{agent.name}' starts with {agent.money} money in {agent.current_city_name}.")

    # 2. Simulation Loop
    for turn in range(1, 101):
        print(f"\n--- Turn {turn} ---")

        # Reload data at the start of the turn
        json_manager()

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
    print(f"Final AI state: Money = {agent.money:.2f}, Inventory = {agent.inventory}")


if __name__ == "__main__":
    run_ai_simulation()
