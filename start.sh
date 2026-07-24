#!/bin/sh

echo "Starting Gunicorn..."
gunicorn --bind 0.0.0.0:5001 app:app &

echo "Starting Nginx..."
nginx -g "daemon off;"
