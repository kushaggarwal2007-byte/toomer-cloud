#!/bin/bash
# Start trading bot in background
python -u toomer_fast_bot.py &
# Start web portal for mobile access
python -u toomer_pro_portal.py
