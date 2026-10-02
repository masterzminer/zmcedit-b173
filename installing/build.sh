# Start the virtual environment
source .venv/bin/activate

# Build the executable from the main mcedit.py file, include the assets folder as read only data
pyinstaller --onefile --add-data "assets:assets" --add-data "LICENSE.txt:." --add-data "README.md:." mcedit.py