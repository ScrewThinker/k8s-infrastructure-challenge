#!/usr/bin/env bash
set -euo pipefail

kubectl run load-generator \
  --namespace infra-challenge \
  --image=busybox:1.37 \
  --restart=Never \
  --rm -i \
  -- /bin/sh -c 'for i in $(seq 1 20); do while true; do wget -q -O- http://challenge-infrastructure-challenge-backend:8000/api/info >/dev/null; done & done; wait'
