"""Training script for the trading bot using PPO."""

import os
import shutil

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

from nre_ai.trading_env import TradingEnv

# Paths
# Source: tests/test_city_data.json (relative to this script)
# Script is in src/nre_ai/
# Root is ../../
# Source is ../../tests/test_city_data.json
SOURCE_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "../../tests/test_city_data.json"
)

# Destination: data/training_cities.json
# We'll put 'data' at the project root for clarity
DEST_DIR = os.path.join(os.path.dirname(__file__), "../../data")
DEST_DATA_PATH = os.path.join(DEST_DIR, "training_cities.json")

MODELS_DIR = "models"
MODEL_NAME = "trading_bot_v1"
LOG_DIR = "logs"


def setup_fresh_data():
    """Copies the source data to a working directory to ensure a fresh start."""
    # Ensure source exists
    if not os.path.exists(SOURCE_DATA_PATH):
        raise FileNotFoundError(f"Source data file not found at {SOURCE_DATA_PATH}")

    # Ensure destination directory exists
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)

    # Remove old destination file if it exists
    if os.path.exists(DEST_DATA_PATH):
        os.remove(DEST_DATA_PATH)
        print(f"Removed old training data at {DEST_DATA_PATH}")

    # Copy source to destination
    shutil.copy2(SOURCE_DATA_PATH, DEST_DATA_PATH)
    print(f"Copied fresh data from {SOURCE_DATA_PATH} to {DEST_DATA_PATH}")


def train():
    """Trains the PPO agent."""
    # 0. Setup Fresh Data
    try:
        setup_fresh_data()
    except FileNotFoundError as e:
        print(f"Error during setup: {e}")
        return

    # 1. Create Environment
    # Use the fresh copy at DEST_DATA_PATH
    env = TradingEnv(cities_json_path=DEST_DATA_PATH)

    # Validate Environment
    check_env(env)
    print("Environment check passed.")

    # 2. Initialize Model
    # MlpPolicy is suitable for vector observations.
    # Added ent_coef to encourage exploration
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=LOG_DIR, ent_coef=0.01)

    # 3. Train
    print("Starting training...")
    # Increased timesteps to allow for better convergence
    model.learn(total_timesteps=300000)
    print("Training finished.")

    # 4. Save Model
    # Ensure models directory exists
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)

    save_path = os.path.join(MODELS_DIR, MODEL_NAME)
    model.save(save_path)
    print(f"Model saved to {save_path}.zip")


if __name__ == "__main__":
    train()
