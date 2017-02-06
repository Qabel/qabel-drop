#!/bin/bash -ue

set -u

pip3 install -qU wheel setuptools pip
pip3 install -qUr requirements.txt
