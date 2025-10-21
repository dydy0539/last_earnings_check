#!/bin/bash
# Test script to run the daily analysis manually
# This allows you to test the analysis without waiting for 8pm

cd "$(dirname "$0")"

echo "=================================================="
echo "Testing Daily Playbook Analysis"
echo "=================================================="
echo ""

python3 daily_playbook_analysis.py

echo ""
echo "=================================================="
echo "Test complete!"
echo "=================================================="

