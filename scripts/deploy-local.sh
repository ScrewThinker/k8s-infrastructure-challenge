#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="infra-challenge"
BACKEND_IMAGE="challenge-backend:local"
FRONTEND_IMAGE="challenge-frontend:local"

: "${APP_TOKEN:=local-demo-token}"

docker build --tag "$BACKEND_IMAGE" backend
docker build --tag "$FRONTEND_IMAGE" frontend
kind load docker-image "$BACKEND_IMAGE" "$FRONTEND_IMAGE" --name "$CLUSTER_NAME"

kubectl create namespace infra-challenge --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic challenge-app-secret \
  --namespace infra-challenge \
  --from-literal=APP_TOKEN="$APP_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install challenge helm/challenge \
  --namespace infra-challenge \
  --set images.backend.repository=challenge-backend \
  --set images.frontend.repository=challenge-frontend \
  --set images.backend.tag=local \
  --set images.frontend.tag=local \
  --atomic --wait --timeout 5m

kubectl get deployment,pod,service,hpa --namespace infra-challenge
