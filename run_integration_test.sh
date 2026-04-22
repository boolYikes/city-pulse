#!/bin/bash

set -a
source .env
set +a

# This is a local integration test unlike pytest
# Make sure ./run_local_infra.sh has been run successfully

invoke_lambda() {
    response=$(curl -X POST \
        "http://localhost:$1/2015-03-31/functions/function/invocations" \
        -d "{
            \"log_level\": \"DEBUG\",
            \"city\": \"NewYork\",
            \"lat\": 40.7698,
            \"lon\": -73.9748,
            \"ts\": \"2026-04-03T14:27:00Z\",
            \"rad\": 12000,
            \"BUCKET\": \"$BUCKET\",
            \"keys\": $2
        }"
    )
    echo "$response"
}

# keys must be a list of strings
# maybe chain | jq -c '.' for messier json
fc_ext_res=$(invoke_lambda 9002 '[]')
aq_ext_res=$(invoke_lambda 9003 '[]')
aq_tf_res=$(invoke_lambda 9004 "$aq_ext_res")
