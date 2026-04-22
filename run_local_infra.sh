#!/bin/bash

NETWORK="city_pulse_net"
docker network create $NETWORK 2>/dev/null

##########
# Lambda #
##########

# Could have used the Lambda image to build Pandas + Pyarrow,
# but it bloats up the handler.zip (100MB per handler)
LAMBDA_IMAGE="xuanminator/lambda-test"

start_lambda() {
    docker ps --format {{.Names}} | grep -q "$1" && docker stop "$1"

    # lambda runtime interface emulator at 8080 -> used to invoke and pass event argument
    docker run \
        --name "$1" \
        --rm -d \
        -p "$3":8080 \
        --env-file .env \
        -e PIPELINE="$4" \
        --network "$NETWORK" \
        "$LAMBDA_IMAGE" \
        "$2"
}

FC_EXT_CONT_NAME="local_lambda_fc_ext"
FC_EXT_HANDLER="lambda.extract.handler.fc_extract_handler"
FC_EXT_PORT=9002
start_lambda "$FC_EXT_CONT_NAME" "$FC_EXT_HANDLER" "$FC_EXT_PORT" "city-test-bronze"

AQ_EXT_CONT_NAME="local_lambda_aq_ext"
AQ_EXT_HANDLER="lambda.extract.handler.aq_extract_handler"
AQ_EXT_PORT=9003
start_lambda "$AQ_EXT_CONT_NAME" "$AQ_EXT_HANDLER" "$AQ_EXT_PORT" "city-test-bronze"

AQ_TF_CONT_NAME="local_lambda_aq_tf"
AQ_TF_HANDLER="lambda.transform.handler.aq_tf_handler"
AQ_TF_PORT=9004
start_lambda "$AQ_TF_CONT_NAME" "$AQ_TF_HANDLER" "$AQ_TF_PORT" "city-test-silver"


#########
# MinIO #
#########

MINIO_CONT_NAME="minio"
docker ps --format {{.Names}} | grep -q $MINIO_CONT_NAME && docker stop $MINIO_CONT_NAME

docker run -d --rm \
 --name $MINIO_CONT_NAME \
 -p 9000:9000 \
 -p 9001:9001 \
 --env-file .env \
 --network $NETWORK \
 quay.io/minio/minio server /data --console-address ":9001"

# health check
for i in {1..10}; do
    if curl -s http://localhost:9000/minio/health/live; then
        echo "MinIO is up!"
        break
    else
        echo "Waiting for MinIO to be up..."
        sleep 2
    fi
done

# create test bucket
set -a
source .env
set +a
docker exec \
    -e MINIO_ROOT_USER \
    -e MINIO_ROOT_PASSWORD \
    -e BUCKET \
    -it minio sh -c '
        mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" &&
        mc mb local/"$BUCKET"
    '

# See readme for the invocation command
