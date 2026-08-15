#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="infra-challenge"
: "${APP_TOKEN:?Set APP_TOKEN before running this script}"

if ! kind get clusters | grep -qx "$CLUSTER_NAME"; then
  kind create cluster --name "$CLUSTER_NAME" --config kind-config.yaml
fi

kubectl config use-context "kind-${CLUSTER_NAME}"

if ! kubectl get deployment metrics-server --namespace kube-system >/dev/null 2>&1; then
  kubectl apply --filename https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.8.1/components.yaml
fi

kubectl patch deployment metrics-server \
  --namespace kube-system \
  --type strategic \
  --patch '{"spec":{"template":{"spec":{"containers":[{"name":"metrics-server","args":["--cert-dir=/tmp","--secure-port=10250","--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname","--kubelet-use-node-status-port","--metric-resolution=15s","--kubelet-insecure-tls"]}]}}}}'
kubectl rollout status deployment/metrics-server --namespace kube-system --timeout=3m

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
