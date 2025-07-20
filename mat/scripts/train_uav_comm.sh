#!/bin/sh
env="uav_communication"
scenario="multi_role_uav"
num_uavs=10
num_gbs=3
num_ues=50
algo="mat"
exp="debug"
seed=1

echo "env is ${env}, scenario is ${scenario}, algo is ${algo}, exp is ${exp}, seed is ${seed}"
python3 mat/scripts/train/train_uav_comm.py --env_name ${env} --scenario_name ${scenario} \
    --algorithm_name ${algo} --experiment_name ${exp} --seed ${seed} \
    --num_uavs ${num_uavs} --num_gbs ${num_gbs} --num_ues ${num_ues} \
    --n_rollout_threads 8 --episode_length 50 --num_mini_batch 1 \
    --num_env_steps 10000000 --ppo_epoch 5 --lr 7e-4 --critic_lr 7e-4 \
    --use_value_active_masks --use_eval --add_value_last_step
