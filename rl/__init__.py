"""PPO reinforcement-learning controller (image step 5).

Module layout follows docs/design.md section 2:

* ``environment``  --- Gym-like serverless control environment (obs/action).
* ``reward``       --- normalized reward with SLA penalty (section 12).
* ``policy``       --- actor-critic network (pure PyTorch).
* ``train_ppo``    --- PPO with GAE and clipped updates.
* ``evaluate_ppo`` --- policy and baseline evaluation metrics.
"""

from rl.environment import ACTIONS, ServerlessEnv
from rl.policy import ActorCritic
from rl.reward import compute_reward
from rl.train_ppo import load_checkpoint, save_checkpoint, train_ppo

__all__ = [
    "ACTIONS",
    "ServerlessEnv",
    "ActorCritic",
    "compute_reward",
    "train_ppo",
    "save_checkpoint",
    "load_checkpoint",
]
