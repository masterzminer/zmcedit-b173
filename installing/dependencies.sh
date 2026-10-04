#!/bin/bash

# To rebuild requirements.txt
# pip install pipreqs
# pipreqs . --ignore .venv --force

pip install -r requirements.txt

# Explicitly add pyinstaller for building the executable
pip install pyinstaller==6.22.3