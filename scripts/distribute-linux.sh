#!/bin/bash

# Change directory to the parent directory of the script's directory
cd "$(dirname "$0")"/..

# You'd have to install `pyinstaller` before running this script.
pyinstaller --onefile --name pixstudio main.py