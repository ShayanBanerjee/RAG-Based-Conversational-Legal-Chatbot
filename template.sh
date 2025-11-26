# Creating directories
mkdir -p src
mkdir -p research
mkdir -p data

# Creating files
touch src/__init__.py
touch src/helper.py
touch src/prompt.py
touch .env
touch setup.py
touch app.py
touch store_index.py
touch research/trials.ipynb
touch requirements.txt

echo "Directories and files created successfully!"

# Setting up virtual environment and installing dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Install project in editable mode (this installs all deps from setup.py)
pip install -r requirements.txt

# Build the wheel
pip install build
python -m build --wheel

# Install the wheel (dynamic name)
pip install dist/*.whl
echo "Virtual environment set up and dependencies installed successfully!"