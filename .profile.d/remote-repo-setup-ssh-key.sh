#!/bin/sh

set -e

mkdir ~/.ssh
echo "$REMOTE_REPO_SETUP_SSH_KEY" >~/.ssh/id_rsa
