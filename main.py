"""Script for processig city data."""
import sys

import data_processor as p


def main(path: str = 'example_data.json'):
    """Main script for city data processing.
    
    Args:
        path (str): path to json file.

    Returns:
        None
    """
    # loader = p.JsonManager("data.json")
    manager = p.JsonManager(path)
    processor = p.CityProcessor(manager)

    processor.process_changes()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        main(path)
    else:
        main()
