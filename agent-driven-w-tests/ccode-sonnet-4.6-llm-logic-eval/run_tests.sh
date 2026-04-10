#!/bin/bash
.venv/bin/python test_coverage.py > /tmp/coverage_output.txt 2>&1
echo "exit: $?"
