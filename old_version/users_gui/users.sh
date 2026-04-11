#!/usr/bin/env bash
cd "$(dirname "$0")"

cd ..
#https://superuser.com/questions/1547228/how-to-activate-python-virtualenv-through-shell-script
set -e
source ../../__python_venv/bin/activate && \
python3 user_cli.py