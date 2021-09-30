#!/bin/bash

exec python3 client.py &
exec python3 receive_cloud.py &
exec python3 pipeline.py &
exec python3 run.py