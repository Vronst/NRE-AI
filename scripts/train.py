"""Script to train a Reinforcement Learning agent for the NRE game."""

import os
import shutil

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import StopTrainingOnNoModelImprovement, EvalCallback
from stable_baselines3.common.monitor import Monitor

from nre_ai.game_env import GameTradingEnv

# --- 1. Configuration ---
# Source of truth
# DATA_PATH is likely a directory, so we join it with the filename
data_dir = os.getenv("DATA_PATH", "submodules/NRE/Assets/Data/Save/")
SOURCE_DATA_PATH = os.path.join(data_dir, "miasta.json")

# Working file for training
CITIES_DATA_PATH = "tests/test_city_data.json"

# Directory to save trained models and logs
MODEL_DIR = "models"
LOG_DIR = "logs"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Model filename
MODEL_NAME = "nre_ppo_bot"
MODEL_SAVE_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

# Training parameters
TOTAL_TIMESTEPS = 200_000

def reset_training_data():
    """Resets the training data file from the source."""
    print(f"Resetting {CITIES_DATA_PATH} from {SOURCE_DATA_PATH}...")
    try:
        shutil.copyfile(SOURCE_DATA_PATH, CITIES_DATA_PATH)
    except FileNotFoundError:
        print(f"Warning: Source file {SOURCE_DATA_PATH} not found. Skipping reset.")

# --- 2. Environment Setup ---
reset_training_data()

print("Setting up the environment...")
# Wrap the environment in a Monitor to track rewards for callbacks
env = Monitor(GameTradingEnv(cities_data_path=CITIES_DATA_PATH))

# --- 3. Callbacks for Early Stopping ---
# Stop training if there is no improvement in the mean reward
stop_train_callback = StopTrainingOnNoModelImprovement(max_no_improvement_evals=5, min_evals=5, verbose=1)
eval_callback = EvalCallback(env, eval_freq=10000, callback_after_eval=stop_train_callback, verbose=1)

# --- 4. Model Training ---
# PPO (Proximal Policy Optimization) is a robust algorithm and a great starting point.
print("Initializing the PPO model...")
# Increased ent_coef to 0.05 to encourage exploration (default is 0.0)
# Adjusted learning_rate to 0.0003 (default) but kept explicit for clarity
model = PPO(
    "MultiInputPolicy", 
    env, 
    verbose=1, 
    tensorboard_log=LOG_DIR,
    ent_coef=0.05,
    learning_rate=0.0003,
    n_steps=2048,
    batch_size=64
)

print(f"Starting training for {TOTAL_TIMESTEPS} timesteps...")
try:
    model.learn(total_timesteps=TOTAL_TIMESTEPS, tb_log_name=MODEL_NAME, callback=eval_callback)
except KeyboardInterrupt:
    print("Training interrupted manually.")
finally:
    reset_training_data()

# --- 5. Save the Trained Model ---
print(f"Training complete. Saving model to {MODEL_SAVE_PATH}.zip")
model.save(MODEL_SAVE_PATH)

print("\n--- Training Finished ---")
print(f"To view training progress, run: tensorboard --logdir {LOG_DIR}")
print(f"The trained bot is saved at: {MODEL_SAVE_PATH}.zip")
