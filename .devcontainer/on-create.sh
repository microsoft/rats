#! /bin/bash
echo "CONFIGURING DIRENV..."
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
eval "$(direnv hook bash)"
mkdir -p ~/.config/direnv/
cp /workspace/$(basename "$(pwd)")/.devcontainer/direnvrc ~/.config/direnv/direnvrc

echo "UV INSTALL"
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'eval "$(uv generate-shell-completion bash)"' >> ~/.bashrc
echo 'eval "$(uvx --generate-shell-completion bash)"' >> ~/.bashrc
echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
echo 'eval "$(uvx --generate-shell-completion zsh)"' >> ~/.zshrc

echo "INSTALLING COPILOT CLI"
curl -fsSL https://gh.io/copilot-install | bash
mkdir -p ~/.copilot/
cp /workspace/$(basename "$(pwd)")/.devcontainer/mcp-config.json ~/.copilot/mcp-config.json

echo "export DISPLAY=:0" >> ~/.bashrc
echo "export DISPLAY=:0" >> ~/.zshrc

directories=("rats-apps" "rats-devtools")
# Loop through each directory
for dir in "${directories[@]}"; do
    echo "UV INSTALL in $dir..."
    cd "$dir" || exit 1
    direnv allow .
    uv sync
    cd - || exit 1
done

echo "CONFIGURING PRE-COMMIT"
pre-commit install --install-hooks
