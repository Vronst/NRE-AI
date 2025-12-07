"""Main script that uses both NRE-AI and NRE-City.

If run, will generate AI that will take its turn and then  will process,
each and every change in cities data to simulate the city's economy.
"""

import os
from argparse import ArgumentParser

from nrecity import CityProcessor, DataManager, EventProcessor

from .agent import AIAgent

PATH: str = os.environ["DATA_PATH"]


def needed_managers(data_manager: DataManager, path: str) -> None:
    data_manager.create_manager(path + "miasta.json")
    data_manager.create_manager(path + "pre_event_miasta.json")


# TODO: here is where ai should be run
def main() -> None:
    """Main function that runs the simulation."""

    parser = ArgumentParser()
    parser.add_argument(
        "--seed", nargs=1, type=int, help="Seed for random number generator"
    )
    parser.add_argument(
        "-r", "--reset", action="store_true", help="Reset the cities"
    )
    parser.add_argument(
        "--skip", action="store_true", help="Skip running the simulation"
    )
    parser.add_argument(
        "-s", "--skip-events", action="store_true", help="Skip events"
    )
    parser.add_argument("-a", "--ai", action="store_true", help="Run the AI")

    print("Processing arguments...")

    args = parser.parse_args()

    print("Adding managers...")

    data_manager = DataManager()
    needed_managers(data_manager, PATH)

    print("Processing...")

    city_processor = CityProcessor(data_manager.get_manager("miasta"))
    event_processor = EventProcessor(reset=args.reset)

    print("Applying changes...")
    if not args.skip:
        city_processor.process_changes()

    print("Choosing events...")
    if not args.skip_events:
        event_processor.run()

    print("Done!")
