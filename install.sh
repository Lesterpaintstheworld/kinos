#!/bin/bash

# Check if this is an update
if [ "$1" = "update" ]; then
    echo "🔄 Updating KinOS..."
    # Pull latest changes
    git pull
    # Update submodules to latest
    git submodule update --remote --merge
    echo "✓ Repository updated"
fi

# Check for .env file (skip check if updating)
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and configure your API keys"
    exit 1
fi

# Check for OpenAI API key (optional)
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "Warning: OpenAI API key not configured in .env"
    echo "OpenAI models will be unavailable"
    echo "To use OpenAI models, add your OpenAI API key to .env file"
fi

# Check for Perplexity API key (optional)
if ! grep -q "PERPLEXITY_API_KEY=pplx-" .env; then
    echo "Warning: Perplexity API key not configured in .env"
    echo "Research capabilities will be disabled"
    echo "To enable research, add your Perplexity API key to .env file"
fi

echo "✓ Environment configuration verified"

# Check Python availability
if ! $(python3 -c 'from utils.fs_utils import FSUtils; print(FSUtils.get_python_command())' 2>/dev/null); then
    echo "Error: Python 3.9+ is required but not found"
    echo "Please install Python 3.9 or later from https://www.python.org/downloads/"
    exit 1
fi

# Verify Python version
MIN_PYTHON_VERSION="3.12.0"
PYTHON_CMD=$(python3 -c 'from utils.fs_utils import FSUtils; print(FSUtils.get_python_command())')
CURRENT_VERSION=$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")

if ! $PYTHON_CMD -c "import sys; from packaging import version; sys.exit(0 if version.parse('$CURRENT_VERSION') >= version.parse('$MIN_PYTHON_VERSION') else 1)"; then
    echo "Error: Python $MIN_PYTHON_VERSION or later is required"
    echo "Current version: $CURRENT_VERSION"
    echo "Please upgrade Python from https://www.python.org/downloads/"
    exit 1
fi

# Check for Cairo
if ! pkg-config --exists cairo; then
    echo "Warning: Cairo graphics library not found"
    echo "Please install Cairo:"
    echo "- Linux: sudo apt-get install libcairo2-dev pkg-config python3-dev"
    echo "- macOS: brew install cairo pkg-config"
fi

echo "🚀 Starting installation..."


# Install/Update Python dependencies
$(python3 -c 'from utils.fs_utils import FSUtils; print(FSUtils.get_python_command())') -m pip install -r requirements.txt --user
if [ $? -ne 0 ]; then
    echo "Error: Python dependencies installation failed"
    exit 1
fi


# Install/Update and build repo-visualizer
cd vendor/repo-visualizer
npm install --legacy-peer-deps
if [ $? -ne 0 ]; then
    echo "Error: repo-visualizer dependencies installation failed"
    exit 1
fi

npm install -g esbuild
if [ $? -ne 0 ]; then
    echo "Error: esbuild installation failed"
    exit 1
fi

mkdir -p dist
npm run build
if [ $? -ne 0 ]; then
    echo "Error: repo-visualizer build failed"
    exit 1
fi
cd ../..

# Create and make kin executable 
echo '#!/bin/bash' > kin
echo 'python "$(dirname "$0")/routes.py" "$@"' >> kin
chmod +x kin

# Create symbolic link for kin command
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo ln -sf "$(pwd)/kin" /usr/local/bin/kin
fi
