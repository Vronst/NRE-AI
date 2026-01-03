"""Main script that uses both NRE-AI and NRE-City.

If run, will generate AI that will take its turn and then  will process,
each and every change in cities data to simulate the city's economy.
"""

import os
import random
from argparse import ArgumentParser

from nrecity import CityProcessor, DataManager, EventProcessor

from .agent import AIAgent
from .bot_state_processor import BotStateProcessor
from .manager import BotManager

PATH: str = os.environ["DATA_PATH"]


def needed_managers(data_manager: DataManager, path: str) -> None:
    """Set up must have managers."""
    data_manager.create_manager(path + "miasta.json")
    data_manager.create_manager(path + "pre_event_miasta.json")


def main() -> None:
    """Main function that runs the simulation."""
    parser = ArgumentParser()
    parser.add_argument(
        "--seed", nargs=1, type=int, help="Seed for random number generator"
    )
    parser.add_argument("-r", "--reset", action="store_true", help="Reset the cities")
    parser.add_argument("--skip", action="store_true", help="Skip running the simulation")
    parser.add_argument("-s", "--skip-events", action="store_true", help="Skip events")
    parser.add_argument(
        "-a",
        "--ai",
        nargs="?",
        default=[2],
        help="Run the AI, number of bots can be passed.",
    )

    print("Processing arguments...")

    args = parser.parse_args()

    print("Adding managers...")

    data_manager = DataManager()
    needed_managers(data_manager, PATH)

    print("Processing...")

    city_processor = CityProcessor(data_manager.get_manager("miasta"))
    event_processor = EventProcessor(reset=args.reset)

    if args.ai is not None:
        print("Processing AI's...")
        bot_processor = BotStateProcessor(PATH)
        bot_manager = BotManager(bot_processor)

        # Handle args.ai being a list (default) or a string (command line arg)
        ai_arg = args.ai
        if isinstance(ai_arg, list):
            ai_arg = ai_arg[0]
        num_bots = int(ai_arg)

        for x in range(num_bots):
            bot_name = "bot" + str(x)
            bot_data = bot_processor.load_bot_state(bot_name)

            if bot_data:
                print(f"Loading existing bot: {bot_name}")
                bot = AIAgent.from_dict(bot_data)
            else:
                print(f"Creating new bot: {bot_name}")
                city: str = random.choice(["Rybnik", "Aleksandria", "Porto", "Afryka"])
                bot = AIAgent(bot_name, 10000, city)

            bot_manager.add_bot(bot)

        bot_manager.run_all_turns(city_processor.get_dict_of_cities("after"))

    print("Applying changes...")
    if not args.skip:
        city_processor.process_changes()

    print("Choosing events...")
    if not args.skip_events:
        event_processor.run()

    print("Done!")
