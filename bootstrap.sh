#!/bin/bash -ue

PY=3.5
VENV=_venv

which git python$PY pip$PY virtualenv >/dev/null

if [ ! -d $VENV ]; then
virtualenv -p python$PY $VENV
fi

echo ". $VENV/bin/activate" > activate.sh
echo "echo \"See 'inv --list' for available tasks.\"" >> activate.sh
chmod +x activate.sh

set +u
. $VENV/bin/activate
set -u

pip$PY install -qU wheel setuptools pip
pip$PY install -qUr requirements.txt

echo "Run '. ./activate.sh' to activate this environment."
