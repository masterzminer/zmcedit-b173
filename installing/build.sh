#!/bin/bash

# Start the virtual environment
source .venv/bin/activate

# Grab the version for the executable name
VERSION=$(cat assets/zmcedit-b173-version.txt)
# Use underscores instead of dots to avoid the file extension being weird
VERSION="${VERSION//./_}"

# Build the executable from the main mcedit.py file, include the assets folder as read only data
pyinstaller --onefile --add-data "assets:assets" --add-data "LICENSE.txt:." --add-data "README.md:." --add-data "filters:filters" mcedit.py --name "zMCEdit-b173-$VERSION"