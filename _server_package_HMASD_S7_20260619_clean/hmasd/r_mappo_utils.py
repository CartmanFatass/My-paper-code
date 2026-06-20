import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# -- Start of distributions.py content --

class FixedCategorical(torch.distributions.Categorical):
    def sample(self):
        return super().sample().unsqueeze(-1)

    def log_probs(self, actions):
        """
        Computes the log probabilities of actions.
        This implementation correctly handles both sequence and non-sequence data
        for simple Discrete action spaces by preserving the batch dimension.
        """
        # actions shape: (T, B, 1) or (B, 1)
        # self.logits shape: (T, B, N) or (B, N)
        # super().log_prob(actions.squeeze(-1)) returns (T, B) or (B,)
        # .unsqueeze(-1) correctly reshapes it to (T, B, 1) or (B, 1)
        return super().log_prob(actions.squeeze(-1)).unsqueeze(-1)

    def mode(self):
        return self.probs.argmax(dim=-1, keepdim=True)

class FixedNormal(torch.distributions.Normal):
    def log_probs(self, actions):
        return super().log_prob(actions).sum(-1, keepdim=True)

    def entropy(self):
        return super().entropy().sum(-1)

    def mode(self):
        return self.mean

class FixedBernoulli(torch.distributions.Bernoulli):
    def log_probs(self, actions):
        return super().log_prob(actions).view(actions.size(0), -1).sum(-1).unsqueeze(-1)

    def entropy(self):
        return super().entropy().sum(-1)

    def mode(self):
        return torch.gt(self.probs, 0.5).float()

class Categorical(nn.Module):
    def __init__(self, num_inputs, num_outputs, use_orthogonal=True, gain=0.01):
        super(Categorical, self).__init__()
        init_method = [nn.init.xavier_uniform_, nn.init.orthogonal_][use_orthogonal]
        def init_(m): 
            return init(m, init_method, lambda x: nn.init.constant_(x, 0), gain)

        self.linear = init_(nn.Linear(num_inputs, num_outputs))

    def forward(self, x, available_actions=None):
        x = self.linear(x)
        if available_actions is not None:
            x[available_actions == 0] = -1e10
        return FixedCategorical(logits=x)

    def evaluate_actions(self, x, action, available_actions=None, active_masks=None):
        dist = self.forward(x, available_actions)
        action_log_probs = dist.log_probs(action)
        
        if active_masks is not None:
            dist_entropy = (dist.entropy() * active_masks).sum() / active_masks.sum()
        else:
            dist_entropy = dist.entropy().mean()
            
        return action_log_probs, dist_entropy

class DiagGaussian(nn.Module):
    def __init__(self, num_inputs, num_outputs, use_orthogonal=True, gain=0.01, args=None):
        super(DiagGaussian, self).__init__()

        init_method = [nn.init.xavier_uniform_, nn.init.orthogonal_][use_orthogonal]
        def init_(m): 
            return init(m, init_method, lambda x: nn.init.constant_(x, 0), gain)

        self.fc_mean = init_(nn.Linear(num_inputs, num_outputs))
        self.logstd = AddBias(torch.zeros(num_outputs))

    def forward(self, x, available_actions=None, deterministic=False):
        action_mean = self.fc_mean(x)
        zeros = torch.zeros_like(action_mean)
        if x.is_cuda:
            zeros = zeros.cuda()
        action_logstd = self.logstd(zeros)
        dist = FixedNormal(action_mean, action_logstd.exp())
        if deterministic:
            action = dist.mean
        else:
            action = dist.sample()
        return action, dist.log_probs(action)

    def evaluate_actions(self, x, action, available_actions=None, active_masks=None):
        action_mean = self.fc_mean(x)
        zeros = torch.zeros_like(action_mean)
        if x.is_cuda:
            zeros = zeros.cuda()
        action_logstd = self.logstd(zeros)
        dist = FixedNormal(action_mean, action_logstd.exp())
        action_log_probs = dist.log_probs(action)
        if active_masks is not None:
            dist_entropy = (dist.entropy() * active_masks).sum() / active_masks.sum()
        else:
            dist_entropy = dist.entropy().mean()
        return action_log_probs, dist_entropy


class TanhDiagGaussian(nn.Module):
    """Tanh-squashed diagonal Gaussian for bounded continuous actions."""

    def __init__(self, num_inputs, num_outputs, use_orthogonal=True, gain=0.01, args=None):
        super(TanhDiagGaussian, self).__init__()
        init_method = [nn.init.xavier_uniform_, nn.init.orthogonal_][use_orthogonal]

        def init_(m):
            return init(m, init_method, lambda x: nn.init.constant_(x, 0), gain)

        self.fc_mean = init_(nn.Linear(num_inputs, num_outputs))
        self.logstd_init = float(getattr(args, "continuous_logstd_init", -1.0))
        self.logstd_min = float(getattr(args, "continuous_logstd_min", -5.0))
        self.logstd_max = float(getattr(args, "continuous_logstd_max", 0.0))
        self.logstd = AddBias(torch.full((num_outputs,), self.logstd_init))
        self.epsilon = 1e-6

    def _distribution(self, x):
        action_mean = self.fc_mean(x)
        action_logstd = torch.clamp(
            self.logstd(torch.zeros_like(action_mean)),
            self.logstd_min,
            self.logstd_max,
        )
        return FixedNormal(action_mean, action_logstd.exp())

    def _squashed_log_probs(self, dist, raw_action, action):
        gaussian_log_probs = dist.log_probs(raw_action)
        jacobian = torch.log(1.0 - action.pow(2) + self.epsilon).sum(-1, keepdim=True)
        return gaussian_log_probs - jacobian

    def forward(self, x, available_actions=None, deterministic=False):
        dist = self._distribution(x)
        raw_action = dist.mean if deterministic else dist.rsample()
        action = torch.tanh(raw_action)
        return action, self._squashed_log_probs(dist, raw_action, action)

    def evaluate_actions(self, x, action, available_actions=None, active_masks=None):
        dist = self._distribution(x)
        bounded_action = torch.clamp(action, -1.0 + self.epsilon, 1.0 - self.epsilon)
        raw_action = torch.atanh(bounded_action)
        action_log_probs = self._squashed_log_probs(dist, raw_action, bounded_action)
        entropy_raw_action = dist.rsample()
        entropy_action = torch.tanh(entropy_raw_action)
        sampled_entropy = -self._squashed_log_probs(
            dist, entropy_raw_action, entropy_action
        ).squeeze(-1)
        if active_masks is not None:
            masks = active_masks.squeeze(-1)
            dist_entropy = (sampled_entropy * masks).sum() / masks.sum().clamp_min(1.0)
        else:
            dist_entropy = sampled_entropy.mean()
        return action_log_probs, dist_entropy

class AddBias(nn.Module):
    def __init__(self, bias):
        super(AddBias, self).__init__()
        self._bias = nn.Parameter(bias.unsqueeze(1))

    def forward(self, x):
        if x.dim() == 2:
            bias = self._bias.t().view(1, -1)
        # Handle 3D tensor for sequence data (T, B, D)
        elif x.dim() == 3:
            bias = self._bias.t().view(1, 1, -1)
        # Handle 4D tensor for image data
        else:
            bias = self._bias.t().view(1, -1, 1, 1)
            
        # The bias will be broadcasted to match the shape of x
        return x + bias

# -- End of distributions.py content --

def init(module, weight_init, bias_init, gain=1):
    weight_init(module.weight.data, gain=gain)
    bias_init(module.bias.data)
    return module

def get_shape_from_obs_space(obs_space):
    if obs_space.__class__.__name__ == 'Box':
        obs_shape = obs_space.shape
    elif isinstance(obs_space, (list, tuple)):
        obs_shape = obs_space
    else:
        # Fallback for other space types that might have a shape attribute
        try:
            obs_shape = obs_space.shape
        except AttributeError:
            raise NotImplementedError(f"Unsupported observation space type: {type(obs_space)}")
    return obs_shape

def check(input):
    if isinstance(input, torch.Tensor):
        return input
    return torch.from_numpy(input)

class ACTLayer(nn.Module):
    def __init__(self, action_space, inputs_dim, use_orthogonal, gain, args=None):
        super(ACTLayer, self).__init__()
        self.multi_discrete = False
        self.action_type = action_space.__class__.__name__

        if action_space.__class__.__name__ == "Discrete":
            action_dim = action_space.n
            self.action_out = Categorical(inputs_dim, action_dim, use_orthogonal, gain)
        elif action_space.__class__.__name__ == "Box":
            action_dim = action_space.shape[0]
            distribution = getattr(args, "continuous_action_distribution", "gaussian")
            if distribution == "tanh_gaussian":
                self.action_out = TanhDiagGaussian(
                    inputs_dim, action_dim, use_orthogonal, gain, args
                )
            else:
                self.action_out = DiagGaussian(
                    inputs_dim, action_dim, use_orthogonal, gain, args
                )
        elif action_space.__class__.__name__ == "MultiDiscrete":
            self.multi_discrete = True
            self.action_dims = action_space.nvec
            self.action_outs = nn.ModuleList([Categorical(inputs_dim, num_actions, use_orthogonal, gain) for num_actions in self.action_dims])
        else:
            raise NotImplementedError

    def forward(self, x, available_actions=None, deterministic=False):
        if self.multi_discrete:
            actions = []
            action_log_probs = []
            for action_out in self.action_outs:
                dist = action_out(x)
                action = dist.mode() if deterministic else dist.sample()
                actions.append(action)
                action_log_probs.append(dist.log_probs(action))
            
            actions = torch.cat(actions, -1)
            action_log_probs = torch.cat(action_log_probs, -1).sum(-1, keepdim=True)
            return actions, action_log_probs
        elif self.action_type == "Discrete":
            dist = self.action_out(x, available_actions)
            action = dist.mode() if deterministic else dist.sample()
            action_log_probs = dist.log_probs(action)
            return action, action_log_probs
        else: # Box
            return self.action_out(x, available_actions, deterministic)

    def evaluate_actions(self, x, action, available_actions=None, active_masks=None):
        if self.multi_discrete:
            action_log_probs = []
            dist_entropy = []
            for i, action_out in enumerate(self.action_outs):
                dist = action_out(x)
                log_prob = dist.log_probs(action[:, i:i+1])
                action_log_probs.append(log_prob)
                dist_entropy.append(dist.entropy())

            action_log_probs = torch.cat(action_log_probs, -1).sum(-1, keepdim=True)
            dist_entropy = torch.cat(dist_entropy, -1).mean()
            return action_log_probs, dist_entropy
        elif self.action_type == "Discrete":
            return self.action_out.evaluate_actions(x, action, available_actions, active_masks)
        else: # Box
            return self.action_out.evaluate_actions(x, action, available_actions, active_masks)

class CNNBase(nn.Module):
    def __init__(self, args, obs_shape):
        super(CNNBase, self).__init__()
        # Simplified CNNBase for compatibility
        self.hidden_size = args.hidden_size
        self.network = nn.Sequential(
            nn.Linear(np.prod(obs_shape), self.hidden_size),
            nn.ReLU(),
            nn.Linear(self.hidden_size, self.hidden_size),
            nn.ReLU()
        )

    def forward(self, x):
        return self.network(x)

class MLPBase(nn.Module):
    def __init__(self, args, obs_shape):
        super(MLPBase, self).__init__()
        self._use_feature_normalization = args.use_feature_normalization
        self.hidden_size = args.hidden_size
        
        obs_dim = obs_shape[0]
        
        init_method = [nn.init.xavier_uniform_, nn.init.orthogonal_][args.use_orthogonal]
        gain = nn.init.calculate_gain('relu')

        def init_(m):
            return init(m, init_method, lambda x: nn.init.constant_(x, 0), gain=gain)

        self.mlp = nn.Sequential(
            init_(nn.Linear(obs_dim, self.hidden_size)),
            nn.ReLU(),
            init_(nn.Linear(self.hidden_size, self.hidden_size)),
            nn.ReLU()
        )

    def forward(self, x):
        return self.mlp(x)

class RNNLayer(nn.Module):
    def __init__(self, inputs_dim, outputs_dim, recurrent_N, use_orthogonal):
        super(RNNLayer, self).__init__()
        self._recurrent_N = recurrent_N
        self._use_orthogonal = use_orthogonal

        self.rnn = nn.GRU(inputs_dim, outputs_dim, num_layers=self._recurrent_N)
        for name, param in self.rnn.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0)
            elif 'weight' in name:
                if self._use_orthogonal:
                    nn.init.orthogonal_(param)
                else:
                    nn.init.xavier_uniform_(param)
        self.norm = nn.LayerNorm(outputs_dim)

    def forward(self, x, hxs, masks):
        # Check if the input is a sequence
        is_sequence = len(x.shape) > 2
        
        if not is_sequence:
            # Non-sequence case: (B, D)
            # Add sequence dimension for GRU
            x = x.unsqueeze(0)
            # Apply masks to hidden states
            hxs = hxs * masks
            hxs = hxs.unsqueeze(0)
            
            x, hxs = self.rnn(x, hxs)
            
            # Remove sequence dimension
            x = x.squeeze(0)
            hxs = hxs.squeeze(0)
        else:
            # Sequence case: (T, B, D)
            T, B, _ = x.shape
            
            # The masks are of shape (T, B), need to be (T, B, 1) for broadcasting
            if masks.dim() == 2:
                masks = masks.unsqueeze(-1)
            
            # Apply masks to hidden states at each time step
            # We can't apply masks to hxs before the loop as hxs is (1, B, H)
            # and masks are (T, B, 1). We let the GRU handle the sequence.
            
            # Reshape hxs for GRU: (num_layers, B, H)
            hxs = hxs.unsqueeze(0)
            
            # Let GRU process the whole sequence. We will handle masking manually if needed,
            # but GRU is often used with packed sequences for efficiency.
            # A simple approach is to let it run and then zero out states where mask is 0.
            # However, the original logic intended to stop gradient flow for done states.
            
            # A more correct way to handle masks with sequences in GRU
            # is to iterate, but that can be slow.
            # Let's try a compromise: process the whole sequence and then apply masks.
            # This is an approximation but avoids manual unrolling.
            
            # The input x is already (T, B, D), which is what GRU expects.
            # The hidden state hxs is (B, H), needs to be (1, B, H).
            
            # The most robust way is to iterate, as the original code did.
            # Let's refine that logic to be cleaner.
            outputs = []
            for i in range(T):
                # Mask the hidden state before feeding it to the next step
                # hxs is (1, B, H)
                hxs = hxs * masks[i]
                
                # x[i] is (B, D), needs to be (1, B, D)
                out, hxs = self.rnn(x[i].unsqueeze(0), hxs)
                outputs.append(out.squeeze(0))
            
            x = torch.stack(outputs, dim=0)
            # The hidden state for the next call is the last hidden state
            hxs = hxs.squeeze(0)

        x = self.norm(x)
        return x, hxs

class PopArt(nn.Module):
    def __init__(self, input_features, output_features, norm_axes=1, beta=0.99999, epsilon=1e-5, device=torch.device("cpu")):
        super(PopArt, self).__init__()
        self.beta = beta
        self.epsilon = epsilon
        self.norm_axes = norm_axes
        self.input_features = input_features
        self.output_features = output_features
        self.tpdv = dict(dtype=torch.float32, device=device)

        self.weight = nn.Parameter(torch.Tensor(output_features, input_features))
        self.bias = nn.Parameter(torch.Tensor(output_features))
        
        self.mean = nn.Parameter(torch.zeros(output_features), requires_grad=False)
        self.mean_sq = nn.Parameter(torch.zeros(output_features), requires_grad=False)
        self.debiasing_term = nn.Parameter(torch.zeros(output_features), requires_grad=False)

        self.reset_parameters()

    def reset_parameters(self):
        torch.nn.init.kaiming_uniform_(self.weight, a=np.sqrt(5))
        if self.bias is not None:
            fan_in, _ = torch.nn.init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / np.sqrt(fan_in)
            torch.nn.init.uniform_(self.bias, -bound, bound)
        self.mean.zero_()
        self.mean_sq.zero_()
        self.debiasing_term.zero_()

    def forward(self, input_vector):
        if type(input_vector) == np.ndarray:
            input_vector = torch.from_numpy(input_vector)
        input_vector = input_vector.to(**self.tpdv)

        return F.linear(input_vector, self.weight, self.bias)

    @torch.no_grad()
    def update(self, input_vector):
        if type(input_vector) == np.ndarray:
            input_vector = torch.from_numpy(input_vector)
        input_vector = input_vector.to(**self.tpdv)
        
        old_mean, old_std = self.mean, self.std
        
        batch_mean = input_vector.mean(dim=tuple(range(self.norm_axes)))
        batch_mean_sq = (input_vector ** 2).mean(dim=tuple(range(self.norm_axes)))

        self.debiasing_term.mul_(self.beta).add_(1.0)
        self.mean.mul_(self.beta).add_(batch_mean * (1.0 - self.beta))
        self.mean_sq.mul_(self.beta).add_(batch_mean_sq * (1.0 - self.beta))

        self.weight.data = self.weight * old_std / self.std
        self.bias.data = (old_std * self.bias + old_mean - self.mean) / self.std

    @property
    def std(self):
        return (self.mean_sq - self.mean ** 2).sqrt().clamp(min=self.epsilon)
    
    def extra_repr(self):
        return 'in_features={}, out_features={}, beta={}, epsilon={}'.format(
            self.input_features, self.output_features, self.beta, self.epsilon)
