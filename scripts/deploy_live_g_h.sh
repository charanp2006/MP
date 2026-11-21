#!/usr/bin/env bash
set -euo pipefail

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    exit 1
  fi
}

require docker
require kubectl
require helm
require faas-cli

TAG="${TAG:-latest}"
FN_IMAGE="fn-checkout-live:${TAG}"
EXPORTER_IMAGE="control-loop-exporter:${TAG}"
NODE="${NODE:-desktop-control-plane}"

echo "[1/7] ensuring namespaces"
kubectl create namespace serverless-mgmt --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace openfaas --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace openfaas-fn --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

echo "[2/7] building images"
docker build -t "${FN_IMAGE}" -f demo/services/Dockerfile.live demo/services
docker build -t "${EXPORTER_IMAGE}" -f monitoring/Dockerfile.exporter .

echo "[3/7] importing images into Docker Desktop Kubernetes node"
docker save "${FN_IMAGE}" | docker exec -i "${NODE}" ctr --namespace k8s.io images import -
docker save "${EXPORTER_IMAGE}" | docker exec -i "${NODE}" ctr --namespace k8s.io images import -

echo "[4/7] installing OpenFaaS and kube-prometheus-stack"
helm repo add openfaas https://openfaas.github.io/faas-netes/ >/dev/null 2>&1 || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
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

echo "[5/7] applying local live manifests"
kubectl apply -f infrastructure/kubernetes/live-namespaces.yaml
kubectl apply -f infrastructure/kubernetes/live-warm-pool.yaml
kubectl apply -f infrastructure/kubernetes/live-service.yaml
kubectl apply -f infrastructure/kubernetes/live-function-deployment.yaml
kubectl apply -f monitoring/kubernetes/control-loop-exporter.yaml
kubectl rollout status deployment/fn-checkout-warm -n serverless-mgmt --timeout=5m
kubectl rollout status deployment/fn-checkout -n openfaas-fn --timeout=5m
kubectl rollout status deployment/control-loop-exporter -n monitoring --timeout=5m

echo "[6/7] validating OpenFaaS gateway routing"
kubectl -n openfaas port-forward svc/gateway 8080:8080 >/tmp/openfaas-gateway-pf.log 2>&1 &
PF_PID=$!
trap 'kill ${PF_PID} >/dev/null 2>&1 || true' EXIT
sleep 5
GW_PASS="$(kubectl -n openfaas get secret basic-auth -o jsonpath='{.data.basic-auth-password}' | base64 --decode)"
faas-cli login --username admin --password "${GW_PASS}" --gateway http://127.0.0.1:8080 --tls-no-verify
faas-cli deploy -f infrastructure/openfaas/stack.public-router.yml --gateway http://127.0.0.1:8080
kubectl -n openfaas-fn set image deployment/fn-checkout fn-checkout="${FN_IMAGE}"
kubectl -n openfaas-fn set env deployment/fn-checkout SERVICE_PORT=8080 FUNCTION_NAME=fn-checkout WARM_REPLICAS=2 ENERGY_PER_MB=0.002
kubectl -n openfaas-fn rollout status deployment/fn-checkout --timeout=5m
curl --fail --silent --show-error "http://admin:${GW_PASS}@127.0.0.1:8080/function/fn-checkout?probe=deploy" >/dev/null

echo "[7/7] installing Grafana dashboard ConfigMap"
kubectl create configmap control-loop-live-dashboard \
  -n monitoring \
  --from-file=control-loop-live.json=monitoring/grafana/dashboards/control-loop-live.json \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap control-loop-live-dashboard -n monitoring grafana_dashboard=1 --overwrite

echo
echo "Live G/H stack deployed."
echo "Port-forwards for manual verification:"
echo "  kubectl -n openfaas port-forward svc/gateway 8080:8080"
echo "  kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80"
echo "  kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "  kubectl -n monitoring port-forward svc/control-loop-exporter 8000:8000"
echo "Grafana login: admin / admin"
