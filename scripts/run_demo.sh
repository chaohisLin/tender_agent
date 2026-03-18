#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python cli.py --tender data/sample_tender.txt
# 全量同步刷新已有 output：
# python cli.py refresh --tender data/sample_tender.txt
