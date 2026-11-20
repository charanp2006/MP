# Live Phase G/H Runbook

This runbook deploys the local live execution + monitoring stack on Docker
Desktop Kubernetes. It is additive: existing dry-run scaffolding remains in
place. `configs/local-live.yaml` extends `configs/project.yaml` and overrides
only the live-control keys.

## Prerequisites already installed

```bash
docker version
kubectl version --client
kubectl config current-context
helm version --short
faas-cli version
docker desktop kubernetes status
```

Expected current context for this runbook: `docker-desktop`.

OpenFaaS Community Edition rejects locally built images through `faas-cli
deploy` with `the Community Edition license agreement only allows public
images`. The gateway function record is therefore registered with a public
router image (`stack.public-router.yml`) and then the resulting Deployment is
patched to the locally imported `fn-checkout-live:latest` image. The OpenFaaS
gateway still routes and authorizes invocations.
`infrastructure/openfaas/stack.live.yml` remains for registries that allow
local/private images.

## One-command deploy

```bash
bash scripts/deploy_live_g_h.sh
```

## Manual deploy (same commands, step by step)

```bash
kubectl create namespace serverless-mgmt --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace openfaas --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace openfaas-fn --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

docker build -t fn-checkout-live:latest -f demo/services/Dockerfile.live demo/services
docker build -t control-loop-exporter:latest -f monitoring/Dockerfile.exporter .
docker save fn-checkout-live:latest | docker exec -i desktop-control-plane ctr --namespace k8s.io images import -
docker save control-loop-exporter:latest | docker exec -i desktop-control-plane ctr --namespace k8s.io images import -

helm repo add openfaas https://openfaas.github.io/faas-netes/ || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
helm repo update

helm upgrade --install openfaas openfaas/openfaas \
  --namespace openfaas \
  --set functionNamespace=openfaas-fn \
  --set generateBasicAuth=true \
  --wait --timeout 10m

GW_BOOTSTRAP_PASS="$(kubectl -n openfaas get secret basic-auth -o jsonpath='{.data.basic-auth-password}' | base64 --decode)"
kubectl -n monitoring create secret generic openfaas-basic-auth \
  --from-literal=password="${GW_BOOTSTRAP_PASS}" \
  --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  -f monitoring/kubernetes/prometheus-values.yaml \
  --wait --timeout 10m

kubectl apply -f infrastructure/kubernetes/live-namespaces.yaml
kubectl apply -f infrastructure/kubernetes/live-warm-pool.yaml
kubectl apply -f infrastructure/kubernetes/live-service.yaml
kubectl apply -f infrastructure/kubernetes/live-function-deployment.yaml
kubectl apply -f monitoring/kubernetes/control-loop-exporter.yaml

kubectl -n openfaas port-forward svc/gateway 8080:8080 >/tmp/openfaas-gateway-pf.log 2>&1 &
GW_PASS="$(kubectl -n openfaas get secret basic-auth -o jsonpath='{.data.basic-auth-password}' | base64 --decode)"
faas-cli login --username admin --password "${GW_PASS}" --gateway http://127.0.0.1:8080 --tls-no-verify
faas-cli deploy -f infrastructure/openfaas/stack.public-router.yml --gateway http://127.0.0.1:8080
kubectl -n openfaas-fn set image deployment/fn-checkout fn-checkout=fn-checkout-live:latest
kubectl -n openfaas-fn set env deployment/fn-checkout SERVICE_PORT=8080 FUNCTION_NAME=fn-checkout WARM_REPLICAS=2 ENERGY_PER_MB=0.002
kubectl -n openfaas-fn rollout status deployment/fn-checkout --timeout=5m
curl --fail --silent --show-error "http://admin:${GW_PASS}@127.0.0.1:8080/function/fn-checkout?probe=deploy"

kubectl create configmap control-loop-live-dashboard \
  -n monitoring \
  --from-file=control-loop-live.json=monitoring/grafana/dashboards/control-loop-live.json \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap control-loop-live-dashboard -n monitoring grafana_dashboard=1 --overwrite
```

## Run the live control loop

Start port-forwards in separate terminals:

```bash
kubectl -n openfaas port-forward svc/gateway 8080:8080
kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80
kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
kubectl -n monitoring port-forward svc/control-loop-exporter 8000:8000
```

Generate invocations and run bounded live decisions:

```bash
for i in 1 2 3 4 5 6 7 8 9 10; do curl "http://127.0.0.1:8080/function/fn-checkout?probe=$i"; done

python -m orchestrator.decision_loop \
  --config configs/local-live.yaml \
  --metrics-source prometheus \
  --use-tft \
  --execute \
  --steps 5
```

The planner runtime in `configs/local-live.yaml` is `stub`. Live E7 evidence
must be labelled `Qwen3 stub proxy / rules`, not real Qwen3 inference.

## Verify

```bash
python scripts/verify_live_g_h.py --config configs/local-live.yaml
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:9090/api/v1/query?query=up
kubectl get pods -A
kubectl -n openfaas logs deploy/gateway
kubectl -n openfaas-fn logs -l faasFunction=fn-checkout --tail=50
```

Grafana: `http://127.0.0.1:3000` with `admin` / `admin`, dashboard title
`Predictive Serverless - Live Control Loop` (UID `control-loop-live`).

## Safety notes

- `configs/project.yaml` keeps `enabled=false`, `dry_run=true`, `allow_live=false`.
- `configs/local-live.yaml` is the only file that enables live execution.
- `LiveKubernetesExecutor` validates action IDs and authorization, restricts
  namespaces, executes bounded `kubectl scale` commands only, supports
  rollback, cooldown, and post-action replica verification.
- Stale Prometheus metrics force `NOOP` in `DecisionLoop.decide()`.
