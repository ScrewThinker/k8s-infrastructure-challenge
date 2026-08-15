# 8–12 minute recording plan

## 0:00–3:15 — Live demo

1. Open `http://localhost:8080`; point out that the React UI displays data and the backend pod name returned through Nginx.
2. Run `kubectl get deploy,pod,svc,hpa -n infra-challenge`.
3. Show `kubectl get application -n argocd` with `Synced` and `Healthy`.
4. Open the latest GitHub Actions run: backend tests, frontend build, two Docker builds, GHCR push, and GitOps tag commit.
5. Open Prometheus at `http://localhost:9090/targets` and query `challenge_http_requests_total`.
6. Show JSON logs with `kubectl logs -n infra-challenge -l app.kubernetes.io/component=backend --tail=5`.

## 3:15–5:30 — Architecture

Explain the request path: browser → Nginx frontend Service → Python backend Service. There is intentionally no database; the backend is the frontend's service dependency.

Explain delivery: push → GitHub-hosted runner tests → two immutable images in GHCR → workflow updates Helm image tags → Argo CD detects Git → Kind converges to desired state.

Show the Helm values/templates rather than hiding Kubernetes resources. Explain probes, CPU/memory requests, HPA (2–5 replicas at 60% CPU), non-root containers, and rolling-update settings.

Explain that `APP_TOKEN` is created directly in the cluster and only referenced by name from Helm. It is never committed to Git.

## 5:30–8:30 — Failure and debugging

Follow `docs/FAILURE-DEMO.md`. State the initial hypothesis, then let evidence narrow it:

1. Observe frontend `CrashLoopBackOff` while backend remains Ready.
2. Describe the pod to eliminate scheduling and image-pull problems.
3. Read Nginx logs and identify upstream DNS failure.
4. List Services and Endpoints to compare configured and actual names.
5. Revert the bad Git commit, watch Argo CD reconcile, and reload the UI.

Mention the useful wrong assumption: an unavailable UI can look like a backend crash, but backend pod state showed the application was healthy before inspecting Nginx.

## 8:30–10:00 — Tradeoffs

- Kind is appropriate for a repeatable demonstration, not control-plane or multi-zone resilience.
- In-cluster Prometheus uses `emptyDir` and two-hour retention; production needs durable remote storage, alerting, and dashboards.
- Kubernetes Secrets are base64-encoded, not encrypted by themselves. Production should use External Secrets with a cloud secret manager and encryption at rest.
- HPA reacts only to CPU. Production scaling should use measured traffic/latency signals and realistic load tests.
- Git rollback is auditable and compatible with Argo CD, but progressive delivery would benefit from Argo Rollouts and automated metric gates.
- Nginx and backend have two replicas, but a single-node Kind cluster cannot protect against node failure.
