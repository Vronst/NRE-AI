"""
Training script for the RL agent using Stable Baselines3.
"""
import os
import shutil
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import DummyVecEnv

from nre_ai.game_env import GameTradingEnv

# Constants
# Use test_city_data.json for training
CITIES_DATA_PATH = "tests/test_city_data.json"

# The source of truth to reset from
data_dir = os.getenv("DATA_PATH", "submodules/NRE/Assets/Data/Save/")
SOURCE_DATA_PATH = os.path.join(data_dir, "miasta.json")

MODELS_DIR = "models/ppo"
LOGS_DIR = "logs"
TIMESTEPS = 100000

def reset_training_data():
    """Resets the training data file from the source."""
    print(f"Resetting {CITIES_DATA_PATH} from {SOURCE_DATA_PATH}...")
    try:
        shutil.copyfile(SOURCE_DATA_PATH, CITIES_DATA_PATH)
    except FileNotFoundError:
        print(f"Warning: Source file {SOURCE_DATA_PATH} not found. Skipping reset.")

def train():
    """
    Sets up and runs the training loop.
    """
    # Create directories for saving models and logs
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Reset data before starting
    reset_training_data()

    # Initialize the environment
    # We use a lambda to delay the creation of the environment until needed
    # The environment itself handles resetting from the file on each episode reset
    env = DummyVecEnv([lambda: GameTradingEnv(cities_data_path=CITIES_DATA_PATH)])

    # Initialize the PPO model
    model = PPO(
        "MultiInputPolicy",
        env,
        verbose=1,
        tensorboard_log=LOGS_DIR,
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
    )

    # Set up a checkpoint callback to save the model every 10,000 steps
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=MODELS_DIR,
        name_prefix="nre_trading_bot"
    )

    # Train the agent
    print("Starting training...")
    try:
        model.learn(total_timesteps=TIMESTEPS, callback=checkpoint_callback)
    finally:
        # Ensure data is reset even if training is interrupted
        reset_training_data()

    print("Training finished.")

    # Save the final model
    model.save(os.path.join(MODELS_DIR, "nre_trading_bot_final"))

    # Close the environment
    env.close()

if __name__ == "__main__":
    train()
