"""
Q-Learning Module for LionAGI QE Fleet

This module provides reinforcement learning capabilities for the 18 specialized
QE agents in the fleet. It implements classic Q-Learning with:

- Bellman equation for Q-value updates
- Epsilon-greedy action selection
- Experience replay for improved sample efficiency
- State encoding and reward calculation
- PostgreSQL persistence for distributed learning

Version: 1.0.0
Author: LionAGI QE Fleet Contributors
"""

from .qlearner import QLearningService
from .state_encoder import StateEncoder
from .reward_calculator import RewardCalculator
from .db_manager import DatabaseManager

__version__ = "1.0.0"

__all__ = [
    "QLearningService",
    "StateEncoder",
    "RewardCalculator",
    "DatabaseManager",
]
