#!/bin/bash
source venv/bin/activate
while true
do
  echo "🔄 Checking stock at $(date)"
  python3 croma_bot.py
  sleep 60
done
