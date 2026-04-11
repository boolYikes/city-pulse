#!/bin/bash

set -a
source .env
set +a

TEST_CONTAINER_NAME="minio"

docker ps --format {{.Names}} | grep -q $TEST_CONTAINER_NAME && docker stop $TEST_CONTAINER_NAME

docker run -d --rm \
 --name $TEST_CONTAINER_NAME \
 -p 9000:9000 \
 -p 9001:9001 \
 -e "MINIO_ROOT_USER=$MINIO_ROOT_USER" \
 -e "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD" \
 quay.io/minio/minio server /data --console-address ":9001"

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
