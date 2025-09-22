#!/bin/bash

# 容器环境一次性配置脚本
# 使用方法：在容器内执行 /path/to/container_setup.sh

set -e  # 遇到错误立即退出

echo "开始配置容器环境..."

# 安装所需依赖
echo "安装系统依赖..."
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    libavutil-dev \
    libavformat-dev \
    libavcodec-dev \
    libpcap-dev \
    libswscale-dev \
    git  # 添加git，因为后面要显示git分支

# 配置忽略大小写自动补齐
echo "配置自动补齐忽略大小写..."
echo 'set completion-ignore-case On' >> ~/.inputrc

# 配置历史命令搜索
echo "配置历史命令搜索..."
cat >> ~/.bashrc <<'EOF'

# Enable up/down arrow history search with prefix
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'
EOF


# 配置Git分支显示
echo "配置Git分支显示..."
cat >> ~/.bashrc << 'EOF'

# ========== 自定义配置 ==========
# Show git branch name
force_color_prompt=yes
color_prompt=yes
parse_git_branch() {
  git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/(\1)/'
}
if [ "$color_prompt" = yes ]; then
  PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[01;31m\]$(parse_git_branch)\[\033[00m\]\$ '
else
  PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w$(parse_git_branch)\$ '
fi
unset color_prompt force_color_prompt
# ========== 自定义配置结束 ==========
EOF

echo "配置完成！"
echo "请执行以下命令使配置生效："
echo "source ~/.bashrc"
