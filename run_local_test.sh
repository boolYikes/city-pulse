#!/bin/bash

for i in {1..10}; do
    if curl -s http://localhost:9000/minio/health/live; then
        echo "MinIO is up!"
        break
    else
        echo "Waiting for MinIO to be up..."
        sleep 2
    fi
done

.venv/bin/python -m pytest -v -s --log-cli-level=INFO
