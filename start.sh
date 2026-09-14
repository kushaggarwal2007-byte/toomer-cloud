#!/bin/bash
python -u toomer_fast_bot.py &
gunicorn --bind 0.0.0.0:8080 toomer_pro_portal:app
