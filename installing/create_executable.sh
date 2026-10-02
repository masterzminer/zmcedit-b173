# Go to the root of the project
cd ..

echo Creating virtual environment
./installing/virtual_env.sh

# Start the virtual environment
source .venv/bin/activate

echo Building nbt module
python pymclevel/build_nbt.py build_ext --inplace

echo Installing pip dependencies
./installing/dependencies.sh

echo Building executable
./installing/build.sh
