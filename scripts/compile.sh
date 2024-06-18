#!/bin/bash

cd "$(dirname "$0")"/..
pyside6-rcc resources.qrc -o resources.py