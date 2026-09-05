# Learner navigation overlay

Start with `q_learner.py` for batched time-unrolls, target computation, masking, optimizer and
target updates. Compare `ppo_learner.py` or `actor_critic_learner.py` for policy/critic loops and
the extra sequential time loop. Follow `../run.py` to see when a learner call occurs and how a
sample is moved to the configured device. All claims require fixed-SHA line checks; preserve
upstream files and report unmeasured acceleration as such.
