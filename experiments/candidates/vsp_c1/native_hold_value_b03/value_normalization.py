"""Training-only scalar population moments; no autograd or optimizer state."""
import torch


class ValueMoments:
    def __init__(self):
        self.n = self.updates = 0
        self.mean = torch.zeros((), dtype=torch.float32)
        self.M2 = torch.zeros((), dtype=torch.float32)

    @property
    def scale(self):
        if self.n == 0:
            return torch.ones((), dtype=torch.float32)
        return (self.M2 / self.n).clamp_min(1e-8).sqrt()

    @torch.no_grad()
    def update(self, targets):
        values = targets.detach().to(device="cpu", dtype=torch.float32).reshape(-1)
        k = values.numel()
        batch_mean = values.mean()
        batch_M2 = (values - batch_mean).square().sum()
        if self.n == 0:
            self.mean, self.M2 = batch_mean, batch_M2
        else:
            delta = batch_mean - self.mean
            total = self.n + k
            self.mean = self.mean + delta * k / total
            self.M2 = self.M2 + batch_M2 + delta * delta * self.n * k / total
        self.n += k
        self.updates += 1

    def decode(self, value):
        return self.mean + self.scale * value

    def normalize(self, targets):
        return ((targets - self.mean) / self.scale).detach()

    def state(self):
        return dict(n=self.n, mean=float(self.mean), M2=float(self.M2),
                    scale=float(self.scale), updates=self.updates)
