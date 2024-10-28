#!/usr/bin/env bash
# Wrapper to run commands for pre-commit inside the coord_transcription_api Docker container

# Exit immediately if a command exits with a non-zero status
set -e

# Check if at least one argument is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <command> [args...]"
    exit 1
fi

# Get the script's directory
SCRIPTPATH="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"

# Execute the command inside the Docker container
docker compose run --rm \
    -v "$SCRIPTPATH/src:/app/src" \
    -v "$SCRIPTPATH/tests:/app/tests" \
    -T coord_transcription_api bash -c "$*"
