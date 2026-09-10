"""Selected EntityAttentionLayer path from thu-rllab/CAMA.

Source: CAMA/modules/layers/attention.py at
1d8d6f8c44102d7b8904bf44eeb38cd1276dbb58. Optional diagnostics,
ranking, repeated attention and pooling are omitted for this fixed object.
"""
import torch
from torch import nn
from torch.nn import functional as F


class EntityAttentionLayer(nn.Module):
    def __init__(self):
        super().__init__()
        self.n_heads = 4
        self.embed_dim = 128
        self.head_dim = 32
        self.register_buffer("scale_factor", torch.scalar_tensor(32).sqrt())
        self.in_trans = nn.Linear(128, 384, bias=False)
        self.out_trans = nn.Linear(128, 128)

    def forward(self, entities, pre_mask, post_mask):
        entities_t = entities.transpose(0, 1)
        n_queries = post_mask.shape[1]
        ne, bs, _ = entities_t.shape
        query, key, value = self.in_trans(entities_t).chunk(3, dim=2)
        query = query[:n_queries]
        query_spl = query.reshape(n_queries, bs * 4, 32).transpose(0, 1)
        key_spl = key.reshape(ne, bs * 4, 32).permute(1, 2, 0)
        value_spl = value.reshape(ne, bs * 4, 32).transpose(0, 1)
        attn_logits = torch.bmm(query_spl, key_spl) / self.scale_factor
        pre_mask_rep = pre_mask[:, :n_queries].repeat_interleave(4, dim=0)
        masked_attn_logits = attn_logits.masked_fill(pre_mask_rep.bool(), -float("inf"))
        attn_weights = F.softmax(masked_attn_logits, dim=2)
        attn_weights = attn_weights.masked_fill(attn_weights != attn_weights, 0)
        attn_outs = torch.bmm(attn_weights, value_spl)
        attn_outs = attn_outs.transpose(0, 1).reshape(n_queries, bs, 128)
        attn_outs = self.out_trans(attn_outs.transpose(0, 1))
        return attn_outs.masked_fill(post_mask.unsqueeze(2).bool(), 0)
