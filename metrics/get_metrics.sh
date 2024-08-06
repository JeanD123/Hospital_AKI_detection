#!/bin/bash

NAMESPACE="manrique"
POD_NAME="aki-detection-7b98b755c4-bn442"
LOCAL_PORT="8000"
LOG_FILE="metrics_log.txt"

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

kubectl -n $NAMESPACE port-forward $POD_NAME $LOCAL_PORT &

sleep 5

METRICS=$(curl -s http://localhost:$LOCAL_PORT/metrics)

echo "Timestamp: $TIMESTAMP" >> $LOG_FILE
echo "$METRICS" >> $LOG_FILE

echo "$METRICS"

pkill -f "kubectl -n $NAMESPACE port-forward $POD_NAME $LOCAL_PORT:$LOCAL_PORT" # kill port-forwarding
