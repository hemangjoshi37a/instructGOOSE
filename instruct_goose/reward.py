# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_reward_model.ipynb.

# %% auto 0
__all__ = ['RewardModel', 'PairwiseLoss']

# %% ../nbs/03_reward_model.ipynb 4
import torch
from torch import nn
from transformers import AutoModel, AutoTokenizer
from torchtyping import TensorType

# %% ../nbs/03_reward_model.ipynb 6
class RewardModel(nn.Module):
    """Reward model."""
    def __init__(
        self, checkpoint: str, # `transformers`'s model path
        dropout: float = 0.1 
    ):
        super().__init__()
        self.model = AutoModel.from_pretrained(checkpoint)
        
        config = self.model.config
        n_embed = config.n_embd
        
        # custom head
        self.reward_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(n_embed, 1),
            nn.Sigmoid()
        )
        
    def forward(
        self,
        input_ids: TensorType["batch_size", "seq_len"],
        attention_mask: TensorType["batch_size", "seq_len"] = None,
    ) -> TensorType["batch_size", 1]: # A reward scalar for each item in a batch
        """Calculate reward for each item in a batch."""
        last_hidden_state = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
        ).last_hidden_state
        
        output = self.reward_head(last_hidden_state)
                
        # for eacb item in the batch
        # choose the hidden state of the last token as a reward!
        reward_scalar = output[:, -1, 0]
        
        return reward_scalar

# %% ../nbs/03_reward_model.ipynb 10
class PairwiseLoss(nn.Module):
    """Pairwise loss function."""
    def forward(
        self,
        chosen_rewards: TensorType["batch_size", 1], # The reward of the chosen prompt
        rejected_rewards: TensorType["batch_size", 1] # The reward of the rejected prompt
    ) -> TensorType[1]: # A scalar loss
        """Forward pass."""
        assert len(chosen_rewards) == len(rejected_rewards)
        batch_size = len(chosen_rewards)
        
        # maps the difference between the rewards to a probability
        probs = torch.sigmoid(chosen_rewards - rejected_rewards)
        return -probs.mean() / batch_size
