#!/usr/bin/env bash
set -e
make install
pip install --upgrade pip
pip install poetry
poetry install