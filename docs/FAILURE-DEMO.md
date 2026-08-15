# Intentional failure: broken service discovery

This failure changes only the frontend's backend hostname. Nginx cannot resolve the nonexistent Kubernetes Service, so the frontend enters `CrashLoopBackOff`. The backend remains healthy, which makes the dependency boundary visible.

## Create the failure

Edit `helm/challenge/values.yaml`:

```yaml
frontend:
  backendHost: "backend-does-not-exist"
```

Commit and push the change. Argo CD will synchronize it automatically.

```bash
git add helm/challenge/values.yaml
git commit -m "demo: break frontend service discovery"
git push
```

## Debug it live

Start broad, then narrow the investigation:

```bash
kubectl get pods -n infra-challenge
kubectl get application infrastructure-challenge -n argocd
kubectl describe pod -n infra-challenge -l app.kubernetes.io/component=frontend
kubectl logs -n infra-challenge -l app.kubernetes.io/component=frontend --tail=30
kubectl get services -n infra-challenge
kubectl get endpointslices -n infra-challenge
kubectl get pods -n infra-challenge -l app.kubernetes.io/component=backend
```

Expected root-cause evidence in the frontend logs:

```text
host not found in upstream "backend-does-not-exist"
```

Reasoning:

1. The frontend pods fail while backend pods remain Ready, so this is not a backend process failure.
2. Image pulls succeed, eliminating registry credentials and image tags.
3. Nginx explicitly reports DNS resolution of its upstream.
4. Services and EndpointSlices prove that the configured name does not exist and reveal the correct Service name.

## Fix and verify

Use Git as the rollback mechanism so desired state and cluster state remain consistent:

```bash
git revert --no-edit HEAD
git push
kubectl get pods -n infra-challenge -w
curl http://localhost:8080/api/info
```

Do not patch the live Deployment as the permanent fix. Argo CD self-healing would restore the broken Git state.
