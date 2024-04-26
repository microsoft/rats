#! /bin/bash
# this runs ONCE after the container is created, and runs in the user's context inside the container
# ===========================

git config -–global core.editor "nano"
git config --global pager.branch false
git config --global alias.ba branch
git config --global alias.co checkout
git config --global alias.st status
git config --global alias.sa stash
git config --global alias.cp cherry-pick
git config --global alias.mt mergetool
git config --global alias.pl pull --rebase
