# Git / GitHub / 云服务器远程实验入门说明

这份文档解释如何用 GitHub 私有仓库管理本地代码，并在云服务器上通过
`git pull` 获取最新代码来运行实验。目标是替代频繁手动打包 zip 的流程。

适用场景：

- 本地 Windows 机器负责改代码、提交代码、推送到 GitHub。
- GitHub 私有仓库负责保存代码版本。
- 云服务器负责拉取代码并运行训练实验。
- VSCode Remote-SSH 负责远程登录服务器、查看文件和日志。

## 1. 先理解这套流程在解决什么问题

以前的流程是：

```text
本地改代码 -> 打包 zip -> 上传服务器 -> 解压 -> 跑实验
```

这个流程容易出问题：

- 打包时可能漏文件，例如 `envs/`、`routing_protocols.py`。
- 多次上传 zip 后，服务器上可能混着旧代码和新代码。
- 很难确认服务器到底运行的是哪一版代码。
- 每次实验都要重新打包，效率低。

使用 GitHub 后，流程变成：

```text
本地改代码 -> git commit -> git push -> 服务器 git pull -> 跑实验
```

好处是：

- 服务器直接从 GitHub 拉最新代码。
- 每次实验对应一个明确的 commit。
- 代码修改有历史记录，出错可以回看或回退。
- 多台服务器可以拉同一个仓库并行跑实验。

## 2. Git、GitHub、SSH key 分别是什么

### Git

Git 是本地代码版本管理工具。它记录：

- 哪些文件改了；
- 每次提交改了什么；
- 谁在什么时候提交；
- 当前代码属于哪个分支。

常用命令：

```bash
git status
git add <file>
git commit -m "message"
git push
git pull
```

### GitHub

GitHub 是远程代码托管平台。你可以把本地 Git 仓库推送到 GitHub 私有仓库。

它的作用类似：

```text
本地仓库 <-> GitHub 私有仓库 <-> 云服务器仓库
```

### SSH key

SSH key 是服务器访问 GitHub 私有仓库的身份证。

它由两部分组成：

```text
私钥：~/.ssh/hmasd_github
公钥：~/.ssh/hmasd_github.pub
```

私钥留在服务器，不能泄露。

公钥放到 GitHub 仓库的 Deploy key 里。GitHub 看到服务器拿着对应私钥来访问时，就允许它拉取私有仓库。

## 3. 在服务器上创建 SSH key

在云服务器终端执行：

```bash
ssh-keygen -t ed25519 -C "hmasd-cloud-runner" -f ~/.ssh/hmasd_github
```

含义：

- `ssh-keygen`：生成 SSH key。
- `-t ed25519`：使用一种较新的密钥算法。
- `-C "hmasd-cloud-runner"`：给这把 key 加一个注释，方便识别。
- `-f ~/.ssh/hmasd_github`：把私钥保存为 `~/.ssh/hmasd_github`。

如果出现：

```text
Enter passphrase (empty for no passphrase):
```

可以直接按两次 Enter，表示不设置密码短语。

原因：云服务器要无人值守跑实验，如果 key 每次都要求输入密码，会影响自动 `git pull`。

## 4. 把公钥加到 GitHub 私有仓库

查看公钥：

```bash
cat ~/.ssh/hmasd_github.pub
```

输出类似：

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... hmasd-cloud-runner
```

整行复制，包括最后的 `hmasd-cloud-runner`。

然后在 GitHub 私有仓库页面：

```text
Settings -> Deploy keys -> Add deploy key
```

填写：

- Title: `hmasd-cloud-runner`
- Key: 粘贴刚才整行公钥

如果服务器只需要拉代码，不需要往 GitHub 推代码，不要勾选 write access。

## 5. 设置服务器 SSH 文件权限

执行：

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/hmasd_github
chmod 644 ~/.ssh/hmasd_github.pub
```

含义：

- `chmod 700 ~/.ssh`：只有当前用户能访问 `.ssh` 文件夹。
- `chmod 600 ~/.ssh/hmasd_github`：私钥只能当前用户读写。
- `chmod 644 ~/.ssh/hmasd_github.pub`：公钥可以被读取。

SSH 对私钥权限很敏感。如果私钥权限太宽，SSH 可能拒绝使用它。

## 6. 配置服务器使用这把 key 访问 GitHub

如果服务器没有 `nano`，可以用下面的命令创建配置文件：

```bash
cat > ~/.ssh/config <<'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/hmasd_github
  IdentitiesOnly yes
EOF
```

含义：

- `Host github.com`：当访问 `github.com` 时使用这段配置。
- `HostName github.com`：真实连接的服务器地址是 GitHub。
- `User git`：GitHub SSH 访问固定使用 `git` 用户。
- `IdentityFile ~/.ssh/hmasd_github`：使用刚才生成的私钥。
- `IdentitiesOnly yes`：只用这把 key，不乱试其他 key。

然后设置配置文件权限：

```bash
chmod 600 ~/.ssh/config
```

## 7. 测试服务器是否能访问 GitHub

执行：

```bash
ssh -T git@github.com
```

第一次可能会问：

```text
Are you sure you want to continue connecting?
```

输入：

```bash
yes
```

成功时会看到类似：

```text
Hi CartmanFatass/My-paper-code! You've successfully authenticated, but GitHub does not provide shell access.
```

这句话的意思是：

- 认证成功；
- GitHub 确认这台服务器可以访问仓库；
- 但 GitHub 不提供普通 shell 登录，这是正常的。

## 8. 在服务器上克隆私有仓库

进入服务器家目录：

```bash
cd ~
```

克隆仓库：

```bash
git clone git@github.com:CartmanFatass/My-paper-code.git HMASD
```

含义：

- `git clone`：从远程仓库复制一份完整代码。
- `git@github.com:CartmanFatass/My-paper-code.git`：你的私有仓库 SSH 地址。
- `HMASD`：把仓库放到服务器的 `~/HMASD` 目录。

进入项目：

```bash
cd ~/HMASD
```

## 9. 以后如何更新服务器代码

本地改完代码后，一般流程是：

```bash
git status
git add <changed-files>
git commit -m "describe your change"
git push origin <branch-name>
```

服务器上更新代码：

```bash
cd ~/HMASD
git fetch origin
git pull --ff-only
```

含义：

- `git fetch origin`：从 GitHub 获取远程分支信息，但不改当前代码。
- `git pull --ff-only`：把服务器代码快进到 GitHub 最新版本。
- `--ff-only`：如果服务器有本地未提交改动导致不能干净更新，就停止，避免自动合并出混乱。

如果服务器只跑实验，最好不要直接在服务器上改代码。

## 10. 如何确认当前服务器代码版本

查看当前分支：

```bash
git branch --show-current
```

查看当前 commit：

```bash
git log -1 --oneline
```

查看是否有未提交改动：

```bash
git status
```

理想状态应该类似：

```text
nothing to commit, working tree clean
```

这表示服务器代码是干净的，适合跑实验。

## 11. 运行 R24 云端实验

确认脚本存在：

```bash
ls scripts/run_r24_qd_null_control_cloud_64env.sh
```

先 dry-run：

```bash
SEEDS=1,2 TOTAL_TIMESTEPS=320000 NUM_ENVS=64 DEVICE=cuda GUARD_MODE=warn \
  bash scripts/run_r24_qd_null_control_cloud_64env.sh --dry-run
```

dry-run 的作用：

- 只打印将要执行的训练命令；
- 不真正启动训练；
- 用来确认参数是否正确。

需要重点看：

- `--num_envs 64`
- `--device cuda`
- `--total_timesteps 320000`
- `--reward_ratio_guard_mode warn`
- `--enable_team_conditioned_qd_probe`
- 没有开启 q_d/q_D reward。

正式运行：

```bash
SEEDS=1,2 TOTAL_TIMESTEPS=320000 NUM_ENVS=64 DEVICE=cuda GUARD_MODE=warn \
  bash scripts/run_r24_qd_null_control_cloud_64env.sh
```

## 12. 用 tmux 保持实验在后台运行

云服务器 SSH 断开后，普通前台命令可能被中断。建议用 `tmux`。

创建 tmux 会话：

```bash
tmux new -s r24_qd
```

进入会话后运行实验：

```bash
cd ~/HMASD
SEEDS=1,2 TOTAL_TIMESTEPS=320000 NUM_ENVS=64 DEVICE=cuda GUARD_MODE=warn \
  bash scripts/run_r24_qd_null_control_cloud_64env.sh
```

让 tmux 转到后台：

```text
Ctrl+b
d
```

重新进入：

```bash
tmux attach -t r24_qd
```

查看有哪些 tmux 会话：

```bash
tmux ls
```

## 13. 实验日志在哪里

默认日志目录：

```text
logs_cloud_r24_qd_null_control_64env
```

每个 seed 会有自己的目录，例如：

```text
logs_cloud_r24_qd_null_control_64env/seed1/r24_qd_null_control_seed1/
logs_cloud_r24_qd_null_control_64env/seed2/r24_qd_null_control_seed2/
```

重要文件：

```text
runner_status.txt       # runner 状态
runner_output.log       # runner 捕获的完整输出
standalone_train.log    # 训练主日志
metrics/train_updates.csv
metadata/run_manifest.json
```

查看 runner 状态：

```bash
find logs_cloud_r24_qd_null_control_64env -name runner_status.txt -print -exec cat {} \;
```

实时查看日志：

```bash
tail -f logs_cloud_r24_qd_null_control_64env/seed1/r24_qd_null_control_seed1/runner_output.log
```

查看最新训练指标：

```bash
tail -n 5 logs_cloud_r24_qd_null_control_64env/seed1/r24_qd_null_control_seed1/metrics/train_updates.csv
```

## 14. 实验结束后下载哪些文件

通常下载这些就够：

```text
metrics/train_updates.csv
standalone_train.log
runner_output.log
runner_status.txt
metadata/run_manifest.json
```

checkpoint 文件，例如：

```text
standalone_process_core_update_*.pt
```

只有在需要 resume 或 eval 时再下载。checkpoint 通常很大，不必每次都传。

## 15. 常见问题

### `nano: command not found`

服务器没装 nano。用：

```bash
cat > ~/.ssh/config <<'EOF'
...
EOF
```

### `Permission denied (publickey)`

常见原因：

- GitHub Deploy key 没加对。
- 复制公钥时漏了一部分。
- `~/.ssh/config` 写错。
- 私钥权限太宽。

检查：

```bash
ssh -T git@github.com
```

### `git pull --ff-only` 失败

说明服务器目录有本地改动，或者远程历史不能直接快进。

先看：

```bash
git status
```

如果服务器只是跑实验，原则上不要在服务器改代码。需要保留实验输出时，把 logs 放到 Git 忽略目录，不要提交。

### 服务器上没有脚本

先确认服务器拉到了最新分支：

```bash
git fetch origin
git branch --show-current
git log -1 --oneline
ls scripts/run_r24_qd_null_control_cloud_64env.sh
```

如果没有，说明本地可能还没 push，或者服务器不在正确分支。

## 16. 推荐日常习惯

本地改代码前：

```bash
git status
```

本地提交前：

```bash
git diff
git status
```

提交：

```bash
git add <files>
git commit -m "short clear message"
git push origin <branch-name>
```

服务器跑实验前：

```bash
cd ~/HMASD
git pull --ff-only
git log -1 --oneline
```

实验命令建议都用脚本，不要临时手打一大串 Python 参数。这样每次实验更可复现。
