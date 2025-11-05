"""Q-Learning Tests Module

Comprehensive test suite for Q-Learning implementation covering:
- State encoding and feature extraction
- Reward calculation with multi-objective functions
- Q-learning algorithm (Bellman equation, epsilon-greedy)
- BaseQEAgent integration with learning
- Concurrent learning across multiple agents

Test Organization:
- conftest.py: Shared fixtures and test utilities
- test_state_encoder.py: State representation tests
- test_reward_calculator.py: Reward computation tests
- test_qlearner.py: Core Q-learning algorithm tests
- test_base_agent_integration.py: Integration tests with BaseQEAgent

Coverage Target: 100% for core Q-learning logic, 90%+ for integration
"""

__all__ = [
    "test_state_encoder",
    "test_reward_calculator",
    "test_qlearner",
    "test_base_agent_integration",
]
