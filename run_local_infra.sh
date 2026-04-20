#!/bin/bash
# Could have used the Lambda image to build Pandas + Pyarrow,
# but it bloats up the handler.zip (100MB per handler)

# Don't expand it to a docker compose ... yet ... 😭

NETWORK="city_pulse_net"
docker network create $NETWORK 2>/dev/null

##########
# Lambda #
##########

# lambda runtime interface emulator at 8080 -> used to invoke and pass event argument
docker run \
    --name local_lambda \
    --rm -d \
    -p 9002:8080 \
    --env-file .env \
    --network $NETWORK \
    xuanminator/lambda-test


#########
# MinIO #
#########

TEST_CONTAINER_NAME="minio"
docker ps --format {{.Names}} | grep -q $TEST_CONTAINER_NAME && docker stop $TEST_CONTAINER_NAME

docker run -d --rm \
 --name $TEST_CONTAINER_NAME \
 -p 9000:9000 \
 -p 9001:9001 \
 --env-file .env \
 --network $NETWORK \
 quay.io/minio/minio server /data --console-address ":9001"

# Invocation:
# curl -X POST "http://localhost:9002/2015-03-31/functions/function/invocations" -d '{"key":"value"}'
