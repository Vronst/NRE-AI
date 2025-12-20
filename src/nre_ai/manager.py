"""Manager for handling multiple AI agents and their persistence."""

from nrecity import City

from nre_ai.agent import AIAgent
from nre_ai.bot_state_processor import BotStateProcessor


class BotManager:
<<<<<<< HEAD
    """Responsible for running multiple AI agents and saving their states."""
=======
    """Coordinating class for running multiple AI agents and saving their states."""
>>>>>>> main

    def __init__(self, processor: BotStateProcessor):
        """Initializes the BotManager.

        Args:
            processor (BotStateProcessor): The processor for saving state.
        """
        self.processor = processor
        self.bots: list[AIAgent] = []

    def add_bot(self, bot: AIAgent):
        """Registers a bot with the manager.

        Args:
            bot (AIAgent): The AI agent instance to add.
        """
        self.bots.append(bot)

    def run_all_turns(self, cities: dict[str, City]):
        """Runs a single turn for all registered agents and saves their states.

        For each bot:
        1. The agent takes its turn (decides, moves, trades).
        2. The agent's state is converted to the game-compatible format.
        3. The state is saved to disk.

        Args:
            cities (dict[str, City]): The current state of all cities.
        """
        for bot in self.bots:
            # 1. Agent thinks and acts
            bot.take_turn(cities)

            # 2. Convert state for export
            bot_data = bot.to_dict()

            # 3. Save state to disk
            self.processor.save_bot_state(bot_data)
