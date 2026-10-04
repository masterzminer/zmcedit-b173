#!/bin/bash

# Create virtual environment called ".venv"
python3 -m venv .venv

# Allow system packages, needed for gtk ui
python3 -m venv --system-site-packages ".venv"