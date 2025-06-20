#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Only activate if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    # Activate the virtual environment
    source "$SCRIPT_DIR/venv/bin/activate"

    # Print confirmation message
    echo "Virtual environment activated successfully!"
    echo "Current Python path: $(which python)"
fi

# Check if we're in Cursor by looking for CURSOR_TERMINAL environment variable
if [ "$CURSOR_TERMINAL" = "true" ]; then
    echo "Starting services in Cursor..."
    # Start the services
    "$SCRIPT_DIR/start_services.sh"
fi 