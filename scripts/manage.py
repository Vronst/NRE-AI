"""Script to manage AI learning."""

import os
import shutil
from argparse import ArgumentParser

import matplotlib.pyplot as plt
import pandas as pd
from nrecity import CityProcessor, JsonManager

from nre_ai.agent import AIAgent
from nre_ai.rl_agent import RLAgent

MODEL_PATH = "models/trading_bot_v1.zip"


def run_ai_simulation():
    """Runs the AI simulation for a number of turns."""
    parser = ArgumentParser()
    parser.add_argument(
        "--use-rl",
        action="store_true",
        help="Use Reinforcement Learning agents instead of rule-based agents.",
    )
    args = parser.parse_args()

    # 1. Initialization
    data_path = os.getenv("DATA_PATH", None)
    if not data_path:
        raise KeyError("Path for json file with city data not provided")

    # Define paths
    # Use the test data from the project's tests directory as the template
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(scripts_dir)
    template_path = os.path.join(project_root, "tests", "test_city_data.json")
    target_path = os.path.join(data_path, "miasta.json")
    plot_path = os.path.join(scripts_dir, "simulation_progress.png")

    # Reset game data
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template file not found at {template_path}. "
            "Please ensure the test data exists."
        )

    print(f"Resetting simulation data from {template_path}...")
    shutil.copy(template_path, target_path)

    # Initialize managers with the fresh file
    json_manager = JsonManager(target_path)
    processor = CityProcessor(json_manager)

    initial_cities = processor.get_dict_of_cities("after")
    initial_city_name = list(initial_cities.keys())[0] if initial_cities else None

    if not initial_city_name:
        print("Error: No cities found in data file.")
        return

    if args.use_rl and os.path.exists(MODEL_PATH):
        print("Using RL Agent.")
        agent = RLAgent(
            name="Bot1", money=1000, initial_city=initial_city_name, model_path=MODEL_PATH
        )
    else:
        print("Using Rule-Based Agent.")
        agent = AIAgent(name="Bot1", money=1000, initial_city=initial_city_name)

    print(f"AI starts with {agent.money} money in {agent.current_city_name}.")

    # Data collection for plotting
    history = []

    # 2. Simulation Loop
    for turn in range(1, 5100):
        print(f"\n--- Turn {turn} ---")

        # Reload data at the start of the turn
        json_manager()

        # Get current state of the world
        # ('after' and 'cities' are identical at this point)
        cities_state = processor.get_dict_of_cities("after")

        # AI takes its turn, modifying the city objects in `cities_state`
        agent.take_turn(cities_state)

        # Record state
        history.append(
            {
                "Turn": turn,
                "Money": agent.money,
                "Inventory_Count": sum(
                    item["quantity"] for item in agent.inventory.values()
                ),
            }
        )

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

    # 3. Generate Plot
    if history:
        df = pd.DataFrame(history)

        plt.figure(figsize=(10, 6))

        # Plot Money
        plt.subplot(2, 1, 1)
        plt.plot(df["Turn"], df["Money"], marker="o", color="b", label="Money")
        plt.title("Bot Progress Over Time")
        plt.ylabel("Money")
        plt.grid(True)
        plt.legend()

        # Plot Inventory Count
        plt.subplot(2, 1, 2)
        plt.plot(
            df["Turn"],
            df["Inventory_Count"],
            marker="x",
            color="r",
            label="Inventory Items",
        )
        plt.xlabel("Turn")
        plt.ylabel("Item Count")
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.savefig(plot_path)
        print(f"Simulation progress graph saved to {plot_path}")


if __name__ == "__main__":
    run_ai_simulation()
