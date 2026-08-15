# Kubernetes Infrastructure Challenge

A production-style demonstration stack built for a 90-minute DevOps challenge:

- React frontend served by Nginx
- Python FastAPI backend
- Docker images published to GitHub Container Registry (GHCR)
- Helm-managed Kubernetes resources on Kind
- GitHub Actions CI/CD with Argo CD GitOps delivery
- HPA, rollback handling, out-of-repository secrets, structured logs, and Prometheus metrics
- Repeatable service-discovery failure and evidence-driven debugging walkthrough

## Architecture

```text
Browser
   │ http://localhost:8080
   ▼
Frontend NodePort → Nginx pods (2)
                         │ /api
                         ▼
                  Backend ClusterIP → FastAPI pods (HPA: 2–5)
                                           │
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
                  JSON stdout logs                   /metrics endpoint
                                                             │
                                                             ▼
                                                        Prometheus

Git push → GitHub Actions → tests → GHCR images → Helm values commit
                                                        │
                                                        ▼
                                             Argo CD → Kind cluster
```

The frontend-to-backend call is the required service dependency. No database is used.

## Prerequisites

Run the Kubernetes commands inside the WSL distribution where these are installed:

- Docker
- Kind
- kubectl
- Helm 3
- Git
- A public GitHub repository with Actions enabled

The workflow needs repository **Actions → General → Workflow permissions → Read and write permissions**. After the first run, make both GHCR packages public so Kind can pull them without registry credentials.

## Validate before deployment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
pytest backend/tests

cd frontend
npm ci
npm run build
cd ..

helm lint helm/challenge
helm template challenge helm/challenge --namespace infra-challenge > /tmp/challenge-rendered.yaml
kubectl apply --namespace infra-challenge --dry-run=client -f /tmp/challenge-rendered.yaml
```

## First local deployment

The existing `infra-challenge` Kind cluster can be used. If it was created without the port mappings in `kind-config.yaml`, use the port-forward commands below, or recreate it explicitly with that configuration.

Install the HPA dependency, create the runtime Secret, install Argo CD, and register the application:

```bash
export APP_TOKEN="$(openssl rand -hex 24)"
chmod +x scripts/*.sh
./scripts/bootstrap-platform.sh
```

Check reconciliation:

```bash
kubectl get application infrastructure-challenge -n argocd
kubectl get deploy,pod,svc,hpa -n infra-challenge
kubectl top pods -n infra-challenge
```

If the Kind cluster does not expose host ports, keep these running in separate terminals:

```bash
kubectl port-forward -n infra-challenge svc/challenge-infrastructure-challenge-frontend 8080:8080
kubectl port-forward -n infra-challenge svc/challenge-infrastructure-challenge-prometheus 9090:9090
```

Then open:

- Application: <http://localhost:8080>
- Backend through frontend: <http://localhost:8080/api/info>
- Prometheus targets: <http://localhost:9090/targets>

For a build that never touches GHCR or Argo CD, use `./scripts/deploy-local.sh`. Do not run the local Helm release and Argo CD ownership of the same namespace at the same time.

## CI/CD deployment flow

`.github/workflows/ci-cd.yml` performs:

1. Backend dependency installation and pytest tests.
2. React dependency installation and production build.
3. Independent backend and frontend Docker builds.
4. Push to GHCR using immutable `sha-<7 characters>` tags.
5. Update both Helm image tags and commit the desired version to `main`.
6. Argo CD notices the commit and synchronizes it to Kind.

GitHub-hosted runners never need access to WSL or its kubeconfig. The pull-based Argo CD agent is the bridge between GitHub and the local cluster.

## Reliability and operational features

### Autoscaling

The backend HPA maintains 2–5 replicas around 60% average requested CPU. Resource requests are mandatory because CPU-utilization HPA calculations depend on them. The 60-second scale-down stabilization window limits replica flapping.

```bash
kubectl get hpa -n infra-challenge -w
./scripts/load-test.sh
```

Tradeoff: CPU is simple and visible but may not correlate with latency or queue pressure. Metrics Server is an additional cluster dependency.

### Rollback handling

Images are immutable and deployments retain five ReplicaSets. For the GitOps path, run the **Roll back deployment** workflow with a known good `sha-xxxxxxx` tag. It commits the old version as current desired state, allowing Argo CD to reconcile without configuration drift.

For a bad configuration commit, use `git revert <commit>` and push. This is preferable to a lasting `kubectl patch`, which Argo CD would correctly undo.

Tradeoff: rollback is auditable but manual. Production progressive delivery should automate rollback against error-rate and latency gates.

### Helm templating

`helm/challenge` templates Deployments, Services, probes, security contexts, resources, HPA, and Prometheus. Environment-specific choices are values, while the Kubernetes resources remain directly inspectable.

```bash
helm lint helm/challenge
helm template challenge helm/challenge -n infra-challenge | less
```

Tradeoff: Helm reduces repeated YAML but adds rendering/debugging complexity.

### Secret management

The chart references an existing `challenge-app-secret`; it never stores secret contents. `bootstrap-platform.sh` creates the Secret from `APP_TOKEN` at runtime. The readiness endpoint refuses traffic when the value is missing.

Tradeoff: a native Kubernetes Secret is only an API object and is base64-encoded, not inherently encrypted. Production should use encryption at rest and External Secrets backed by Vault or a cloud secret manager.

### Logging and monitoring

The backend emits single-line JSON logs to stdout, collected through Kubernetes' normal container log path:

```bash
kubectl logs -n infra-challenge -l app.kubernetes.io/component=backend --tail=20
```

Prometheus scrapes `/metrics` every 10 seconds. Useful queries:

```promql
challenge_http_requests_total
rate(challenge_http_requests_total[1m])
histogram_quantile(0.95, sum by (le) (rate(challenge_http_request_duration_seconds_bucket[5m])))
```

Tradeoff: the demo Prometheus uses ephemeral storage and no alert manager. It proves instrumentation and scraping, not a production monitoring service.

## Intentional failure walkthrough

Use [docs/FAILURE-DEMO.md](docs/FAILURE-DEMO.md). It intentionally configures a nonexistent backend Service name, producing a real Nginx DNS/startup failure. The walkthrough starts with workload health, then checks events, logs, Services, and Endpoints before reverting the bad Git state.

## Video guide

Use [docs/VIDEO-SCRIPT.md](docs/VIDEO-SCRIPT.md) for a timed 8–12 minute recording that covers the live system, architecture, failure diagnosis, recovery, and production tradeoffs.

## Production limitations

- Kind is single-machine infrastructure and does not demonstrate multi-zone or control-plane resilience.
- Prometheus data is ephemeral and there is no alert routing.
- The app Secret is external to Git but should be sourced from a dedicated secret manager.
- NodePort/port-forwarding is demo routing; production would use an ingress controller, TLS, DNS, and network policies.
- The frontend and backend are intentionally small, and the backend holds no state.
- CI action versions use release tags for readability; a hardened supply chain should pin action commit SHAs, sign images, generate SBOMs, and scan them.
