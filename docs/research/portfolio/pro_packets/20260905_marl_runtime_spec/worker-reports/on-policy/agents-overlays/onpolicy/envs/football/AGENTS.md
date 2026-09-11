# Local HMASD navigation overlay

`Football_Env.py` adapts Google Research Football to per-agent observation/action spaces, rewards,
dones, and info fields. The train entry point chooses dummy or Pipe-backed subprocess vectors and
the shared/separated runners consume the resulting arrays. This local overlay indexes the fixed
snapshot; source remains read-only.
