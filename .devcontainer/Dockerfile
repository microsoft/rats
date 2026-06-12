FROM nvcr.io/nvidia/cuda:13.3.0-cudnn-devel-ubuntu24.04

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64
ENV NCCL_DEBUG=INFO
ENV HOROVOD_GPU_ALLREDUCE=NCCL

RUN apt-get -qq update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get -qq clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/*

RUN apt-get -qq update \
    && apt-get -qq install --no-install-recommends \
    python3-dev apt-transport-https ca-certificates curl wget gnupg lsb-release sudo git zsh \
    openssh-server openssh-client tmux fzf direnv neovim xdg-utils \
    && apt-get -qq clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

RUN mkdir -p -m 755 /etc/apt/keyrings \
    && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && curl -sLS https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | tee /etc/apt/keyrings/microsoft.gpg > /dev/null \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc \
    && curl -fsSL https://packagecloud.io/github/git-lfs/gpgkey | gpg --dearmor -o /etc/apt/keyrings/github_git-lfs-archive-keyring.gpg \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /usr/share/keyrings/nodesource.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/microsoft.gpg \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && chmod go+r /etc/apt/keyrings/github_git-lfs-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/nodesource.gpg \
    && arch=$(dpkg --print-architecture) \
    && node_version=24.x \
    && echo "deb [arch=$arch signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/azure-cli.list > /dev/null \
    && echo "deb [arch=$arch signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/ubuntu/$(lsb_release -rs)/prod $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/microsoft-prod.list > /dev/null \
    && echo "deb [arch=$arch signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && echo "deb [arch=$arch signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && echo "deb [arch=$arch signed-by=/etc/apt/keyrings/github_git-lfs-archive-keyring.gpg] https://packagecloud.io/github/git-lfs/ubuntu/ $(. /etc/os-release && echo "$VERSION_CODENAME") main" | tee /etc/apt/sources.list.d/github_git-lfs.list > /dev/null \
    && cat <<EOF | tee /etc/apt/sources.list.d/nodesource.sources > /dev/null
Types: deb
URIs: https://deb.nodesource.com/node_$node_version
Suites: nodistro
Components: main
Architectures: $arch
Signed-By: /usr/share/keyrings/nodesource.gpg
EOF

RUN apt-get -qq update \
    && apt-get -qq install --no-install-recommends azure-cli gh \
    docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin git-lfs nodejs \
    && apt-get -qq clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*
