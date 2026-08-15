#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="infra-challenge"
: "${APP_TOKEN:?Set APP_TOKEN before running this script}"

if ! kind get clusters | grep -qx "$CLUSTER_NAME"; then
  kind create cluster --name "$CLUSTER_NAME" --config kind-config.yaml
fi

kubectl config use-context "kind-${CLUSTER_NAME}"

helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm repo update >/dev/null
helm upgrade --install metrics-server metrics-server/metrics-server \
  --namespace kube-system \
  --set args[0]=--kubelet-insecure-tls \
  --set args[1]=--kubelet-preferred-address-types=InternalIP \
  --wait --timeout 3m

kubectl create namespace infra-challenge --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic challenge-app-secret \
  --namespace infra-challenge \
  --from-literal=APP_TOKEN="$APP_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply --server-side --force-conflicts \
  --namespace argocd \
  --filename https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl rollout status deployment/argocd-server --namespace argocd --timeout=5m
kubectl apply --filename argocd/application.yaml

echo "Platform ready. Argo CD will sync the application from main."
