#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python -m app.cli demo --tender data/sample_tender.txt
