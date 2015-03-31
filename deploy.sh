#!/bin/bash

export TZ=Europe/Rome

. ./venv/bin/activate

echo "Check if new libraries are needed..."
pip install -r requirements.txt

# MULTITHREAD WITH GUNICORN #
echo "Restarting gunicorn..."
pkill gunicorn
nohup gunicorn fbvoting.__main__:debugged_app -w 10 -k gevent -b 127.0.0.1:3000 >stdout.log 2>&1 &

## redis clean
echo "Cleaning redis chache..."
redis-cli FLUSHALL

echo "Done."