#!/bin/bash
source venv/bin/activate
while true
do
  echo "🔄 Checking stock at $(date)" | tee -a log.txt
  python3 croma_bot.py >> log.txt 2>&1
  sleep 60
done
