#! /bin/bash
# this runs ONCE at devcontainer creation time, and it runs during pre-build phase which
# means it does not have access to user context
# ===========================

# finish config of direnv settings (would be nice to improve the devcontainer "feature")
echo "CONFIGURING DIRENV..."
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
eval "$(direnv hook bash)"
mkdir -p ~/.config/direnv/
cp /workspaces/rats/.devcontainer/direnvrc ~/.config/direnv/direnvrc

echo "INSTALLING COMMITIZEN"
pipx install commitizen
pipx inject commitizen cz-conventional-gitmoji
echo 'eval "$(register-python-argcomplete cz)"' >> ~/.zshrc
echo 'eval "$(register-python-argcomplete cz)"' >> ~/.bashrc

direnv allow .
poetry config virtualenvs.in-project true

directories=("rats-apps" "rats-devtools" "rats-pipelines" "rats-processors", "rats-examples-sklearn")
# Loop through each directory
for dir in "${directories[@]}"; do
    echo "POETRY INSTALL in $dir..."
    cd "$dir" || exit 1
    direnv allow .
    poetry install
    cd - || exit 1
done

echo "CONFIGURING PRE-COMMIT"
pre-commit install --install-hooks
