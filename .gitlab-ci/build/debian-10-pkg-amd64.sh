#!/bin/sh

set -e

if [ "$1" = "setup" ]
then
  true
else
  set -x
  # when changes are applied, git is left in detached state.
  # to change back from the scratch branch and clean up,
  # the dev script needs to have a base branch.
  git status
  git branch -D cibase || true
  git branch -D lavadevscratch || true
  git checkout -b cibase
  git status
  export GIT_COMMITTER_NAME="lava-dev debian build script"
  export GIT_COMMITTER_EMAIL="lava-dev@lavasoftware.org"
  export GIT_AUTHOR_NAME="lava-dev debian build script"
  export GIT_AUTHOR_EMAIL="lava-dev@lavasoftware.org"
  # build the full package, including original source for buster.
  ./share/debian-dev-build.sh -o build -s buster
  debc $(find build -name 'lava_*_amd64.changes' 2>/dev/null|head -n1)
  git branch -D cibase || true
fi
